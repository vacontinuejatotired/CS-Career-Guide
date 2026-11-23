"""离线替换依赖模块，验证超时映射与调用配置；不读取真实环境。"""
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from career_platform.gateway import JsonModelGateway


class JsonGatewayTests(unittest.TestCase):
    def dependencies(self, error=None):
        class ProviderTimeout(Exception):
            pass
        factory = Mock()
        factory.return_value.invoke.return_value = SimpleNamespace(content='{"ok":true}')
        if error:
            factory.return_value.invoke.side_effect = ProviderTimeout('PRIVATE-provider-error')
        modules = {name: ModuleType(name) for name in
                   ('langchain_openai', 'openai', 'cs_career_guide.ai_config')}
        modules['langchain_openai'].ChatOpenAI = factory
        modules['openai'].APITimeoutError = ProviderTimeout
        modules['cs_career_guide.ai_config'].get_llm_kwargs = lambda: {'timeout': 30}
        return modules, factory

    def test_single_call_no_automatic_retry_and_json_parse(self):
        modules, factory = self.dependencies()
        with patch.dict(sys.modules, modules):
            self.assertEqual(JsonModelGateway().generate(system='规则', payload={'answer': '测试'}), {'ok': True})
        factory.assert_called_once_with(temperature=0, max_retries=0, timeout=30)
        self.assertEqual(factory.return_value.invoke.call_count, 1)

    def test_provider_timeout_maps_to_builtin_timeout_without_diagnostics(self):
        modules, factory = self.dependencies(error=True)
        with patch.dict(sys.modules, modules), self.assertRaises(TimeoutError) as error:
            JsonModelGateway().generate(system='规则', payload={})
        self.assertNotIn('PRIVATE', str(error.exception))
        self.assertEqual(factory.return_value.invoke.call_count, 1)
