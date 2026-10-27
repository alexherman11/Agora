import json
from pathlib import Path
from unittest.mock import patch
import pytest
from kernel_runtime_record import KernelRecord
from runtime_pin import PinRefused

def config(tmp_path,url='http://127.0.0.1:8810'):
    path=tmp_path/'mcp.json'
    path.write_text(json.dumps({'mcpServers':{'agora':{'env':{'AGORA_URL':url,'AGORA_BEARER_TOKEN':'fixture'}}}}))
    return path

@pytest.mark.parametrize('url',['https://example.invalid','http://127.0.0.1@remote.invalid','http://127.0.0.1:8810/path','http://127.0.0.1:8810?x=1'])
def test_external_or_ambiguous_record_target_refused_before_io(tmp_path,url):
    with patch('kernel_runtime_record.build_opener') as network:
        with pytest.raises(PinRefused):KernelRecord(config(tmp_path,url))
        network.assert_not_called()

def test_same_checker_used_for_kernel_configuration(tmp_path):
    import codex_worker
    path=config(tmp_path)
    with patch('runtime_pin.Checker') as checker:
        checker.return_value.check.side_effect=RuntimeError('captured unchanged checker')
        with pytest.raises(RuntimeError,match='unchanged checker'):
            codex_worker.runtime_config(tmp_path,mcp=path)
        assert isinstance(checker.call_args.kwargs['record'],KernelRecord)
        checker.return_value.check.assert_called_once_with()

def test_receipt_uses_existing_auth_and_stable_press(tmp_path):
    from io import BytesIO
    sink=KernelRecord(config(tmp_path))
    with patch('kernel_runtime_record.build_opener') as opener:
        opener.return_value.open.side_effect=[BytesIO(b'{"ok":true}'),BytesIO(b'{"ok":true}')]
        for _ in range(2):sink('notice','key',{'reason':'fixture'})
        calls=opener.return_value.open.call_args_list
        assert json.loads(calls[0].args[0].data)==json.loads(calls[1].args[0].data)
        assert calls[0].args[0].headers['Authorization']=='Bearer fixture'
        assert calls[0].args[0].full_url=='http://127.0.0.1:8810/do'
