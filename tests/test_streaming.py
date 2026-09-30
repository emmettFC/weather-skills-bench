import json
import httpx
import pytest
from weather_bench.transport import stream_completion


def test_stream_comments_usage_and_split_content(tmp_path):
    chunks=[{'id':'g','provider':'P','choices':[{'index':0,'delta':{'content':'{"action":'}}]},
            {'choices':[{'index':0,'delta':{'content':'"submit"}'},'finish_reason':'stop'}]},
            {'usage':{'cost':.1,'total_tokens':20},'choices':[]}]
    body=': OPENROUTER PROCESSING\n\n'+''.join('data: '+json.dumps(x)+'\n\n' for x in chunks)+'data: [DONE]\n\n'
    with httpx.Client(transport=httpx.MockTransport(lambda r:httpx.Response(200,headers={'content-type':'text/event-stream'},text=body))) as c:
        _,p=stream_completion(c,{},10,tmp_path/'partial.json')
    assert p['choices'][0]['message']['content']=='{"action":"submit"}'
    assert p['usage']['cost']==.1 and p['provider']=='P'
    assert not (tmp_path/'partial.json').exists()


def test_truncated_stream_journals_but_never_returns_action(tmp_path):
    body='data: '+json.dumps({'id':'g','choices':[{'delta':{'content':'{"action":"submit"}'},'finish_reason':'stop'}]})+'\n\n'
    with httpx.Client(transport=httpx.MockTransport(lambda r:httpx.Response(200,headers={'content-type':'text/event-stream'},text=body))) as c:
        with pytest.raises(httpx.RemoteProtocolError):stream_completion(c,{'model':'m'},10,tmp_path/'partial.json')
    assert json.loads((tmp_path/'partial.json').read_text())['complete'] is False


def test_stream_error_preserved(tmp_path):
    chunk={'error':{'code':503},'usage':{'cost':.03},'choices':[{'delta':{},'finish_reason':'error'}]}
    with httpx.Client(transport=httpx.MockTransport(lambda r:httpx.Response(200,headers={'content-type':'text/event-stream'},text='data: '+json.dumps(chunk)+'\n\n'))) as c:
        _,p=stream_completion(c,{},10,tmp_path/'partial.json')
    assert p['error']['code']==503 and p['usage']['cost']==.03
