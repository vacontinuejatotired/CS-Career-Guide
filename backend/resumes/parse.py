import base64
import io
import json
import logging

logger = logging.getLogger(__name__)

PARSE_PROMPT = (
    '这是一份候选人简历。请只依据简历中可见的文字提取信息，不要猜测或补全，只输出一个 JSON 对象：\n'
    '{"target_role":"目标岗位","years":"工作年限","skills":"核心技能（顿号分隔）",'
    '"education":["学校、专业、学历、时间"],'
    '"experience":["公司、职位、时间、职责"],'
    '"projects":["项目名称、角色、时间、成果"]}\n'
    'education、experience、projects 最多各 3 项，每项不超过 120 字；'
    '缺失的文本字段填空字符串，缺失的列表填空数组。'
    '只要页面中出现“简历”、候选人姓名、目标岗位或联系方式中的任一项，就要正常提取，'
    '不能仅因为字段少而返回降级；只有完全空白、无法阅读或明确不是简历时，'
    '才输出 {"degraded":true}。'
)

ALLOWED_EXTS = ('.pdf', '.jpg', '.jpeg', '.png', '.webp')


def _file_to_images(file_obj, ext):
    """统一转成 PIL 图片列表：图片直接用，PDF 用 PyMuPDF 渲染（最多 5 页）。"""
    import fitz
    from PIL import Image

    file_obj.seek(0)
    data = file_obj.read()
    if ext == '.pdf':
        document = fitz.open(stream=data, filetype='pdf')
        images = []
        for page in list(document)[:5]:
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            images.append(Image.open(io.BytesIO(pixmap.tobytes('png'))))
        document.close()
        return images
    return [Image.open(io.BytesIO(data))]


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
        if start < 0 or end <= start:
            return {'degraded': True}
        record = json.loads(text[start:end])
        if record.get('degraded'):
            return {'degraded': True}
        for key in ('education', 'experience', 'projects'):
            value = record.get(key)
            record[key] = value if isinstance(value, list) else []
        for key in ('target_role', 'years', 'skills'):
            record[key] = str(record.get(key) or '').strip()
        record['degraded'] = False
        return record
    except Exception as e:
        logger.error(f'简历视觉解析失败: {e}')
        return {'degraded': True}
