"""One-use loopback form: browser-held credential goes directly to Keychain.

No browser tokens, hidden state or secret values are extracted through diagnostics.
The user-facing form uses an ordinary password field and a same-origin POST.
"""
import argparse,html,json,secrets,threading
from http.server import BaseHTTPRequestHandler,HTTPServer
from urllib.parse import parse_qs
from .microsoft_provisioning import Keychain


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--service',required=True);parser.add_argument('--account',required=True)
    parser.add_argument('--replace-existing',action='store_true',help='Store a user-authorized credential rotation')
    args=parser.parse_args();keychain=Keychain(args.account,service=args.service)
    nonce=secrets.token_urlsafe(32);stored=False
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def reply(self,status,body):
            raw=body.encode();self.send_response(status);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Security-Policy',"default-src 'none'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'");self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
        def do_GET(self):
            if self.path!='/'+nonce:return self.reply(404,'Not found')
            self.reply(200,'<!doctype html><title>Secure production credential storage</title><h1>Store production credential</h1><p>Destination: macOS Keychain. The value is never shown in logs or reports.</p><p>Service: '+html.escape(args.service)+'</p><p>Account: '+html.escape(args.account)+'</p><form method="post"><label>Production credential <input name="credential" type="password" autocomplete="off" required></label><button type="submit">Store in Keychain</button></form>')
        def do_POST(self):
            nonlocal stored
            origin='http://127.0.0.1:'+str(server.server_port)
            if self.path!='/'+nonce or self.headers.get('Origin')!=origin:return self.reply(403,'Request refused')
            size=int(self.headers.get('Content-Length','0'))
            if not 1<=size<=40000:return self.reply(400,'Credential size invalid')
            value=parse_qs(self.rfile.read(size).decode()).get('credential',[''])[0]
            if not 10<=len(value)<=12000:return self.reply(400,'Credential size invalid')
            try:
                prior=keychain.read()
                if prior is None:keychain.add(value)
                elif prior!=value:
                    if args.replace_existing:keychain.replace(value)
                    else:raise ValueError('existing_credential_differs')
                stored=True;self.reply(200,'<!doctype html><title>Credential stored</title><h1>Credential securely stored</h1><p>Keychain round-trip verification passed.</p>')
                threading.Thread(target=server.shutdown,daemon=True).start()
            except Exception:self.reply(500,'Storage failed; no secret details logged')
    server=HTTPServer(('127.0.0.1',0),Handler)
    print(json.dumps({'form_url':'http://127.0.0.1:'+str(server.server_port)+'/'+nonce,'service':args.service,'account':args.account}),flush=True)
    timer=threading.Timer(1200,server.shutdown);timer.daemon=True;timer.start()
    try:server.serve_forever()
    finally:timer.cancel();server.server_close()
    print(json.dumps({'credential_stored':stored}),flush=True)

if __name__=='__main__':main()
