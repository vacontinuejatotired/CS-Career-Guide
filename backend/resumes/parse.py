import json, io, base64, logging
from pdf2image import convert_from_bytes

logger = logging.getLogger(__name__)

PARSE_PROMPT = (
    '这是一份候选人简历。请阅读并提取信息，只输出 JSON，格式：\n'
    '{"target_role":"目标岗位","years":"工作年限","skills":"核心技能(顿号分隔)",'
    '"projects":["项目描述1","项目描述2","项目描述3"]}\n'
    'projects 最多 3 个，每个不超过 100 字。'
    '图片模糊或不是简历时只输出 {"degraded": true}。'
)

ALLOWED_EXTS = ('.pdf', '.jpg', '.jpeg', '.png', '.webp')


def _file_to_images(file_obj, ext):
    """统一转成 PIL 图片列表：图片直接用，PDF 逐页转（最多 5 页）。"""
    from PIL import Image
    file_obj.seek(0)
    data = file_obj.read()
    if ext == '.pdf':
        return convert_from_bytes(data, dpi=150)[:5]
    return [Image.open(io.BytesIO(data))]        # webp 需 pillow 支持，已内置


def parse_resume_file(file_obj, ext) -> dict:
    """视觉模型解析简历文件 → 结构化 dict。任何失败收敛为 degraded。"""
    if ext not in ALLOWED_EXTS:
        return {'degraded': True}
    try:
        images = _file_to_images(file_obj, ext)
    except Exception as e:
        logger.error(f'简历转图片失败: {e}')
        return {'degraded': True}

    # 复用项目的 LLM 配置（ai_config.get_llm_kwargs）
    from langchain_openai import ChatOpenAI
    from cs_career_guide.ai_config import get_llm_kwargs

    content = [{'type': 'text', 'text': PARSE_PROMPT}]
    for img in images:
        buf = io.BytesIO()
        img.convert('RGB').save(buf, format='JPEG', quality=85)
        b64 = base64.b64encode(buf.getvalue()).decode()
        content.append({'type': 'image_url',
                        'image_url': {'url': f'data:image/jpeg;base64,{b64}'}})

    try:
        llm = ChatOpenAI(temperature=0.1, max_tokens=1000, **get_llm_kwargs())
        resp = llm.invoke([{'role': 'user', 'content': content}])
        text = resp.content
        start, end = text.find('{'), text.rfind('}') + 1
        record = json.loads(text[start:end])
        if record.get('degraded'):
            return {'degraded': True}
        record.setdefault('projects', [])
        record['degraded'] = False
        return record
    except Exception as e:
        logger.error(f'简历视觉解析失败: {e}')
        return {'degraded': True}
