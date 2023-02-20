import yaml
import base64
from oic import rndstr
from oic.oic.message import AuthorizationResponse
from oidc import get_oidc_client
from flask import Flask
from flask import redirect, request, session, make_response

response_format = '''mkdir -p ~/.kube
cat << EOF > ~/.kube/config
{}
EOF
chmod 600 ~/.kube/config'''


def get_kubeconfig(
    ca,
    host,
    name,
    user_email,
    client_id,
    client_secret,
    id_token,
    issuer,
    refresh_token,
):
    return {
        'apiVersion': 'v1',
        'clusters': [
            {
                'cluster': {
                    'certificate-authority-data': ca,
                    'server': host,
                },
                'name': name
            }
        ],
        'contexts': [
            {
                'context': {
                    'cluster': name,
                    'user': user_email
                },
                'name': user_email
            }
        ],
        'current-context': user_email,
        'kind': 'Config',
        'preferences': {},
        'users': [
            {
                'name': user_email,
                'user': {
                    'auth-provider': {
                        'config': {
                            'client-id': client_id,
                            'client-secret': client_secret,
                            'id-token': id_token,
                            'idp-issuer-url': issuer,
                            'refresh-token': refresh_token,
                        },
                        'name': 'oidc'
                    }
                }
            }
        ]
    }


def create_app(config_path):
    with open(config_path, 'r') as f:
        config = yaml.full_load(f)

    app = Flask(__name__)
    app.secret_key = base64.b64decode(
        bytes(config['flask_secret_key'], encoding='utf-8')
    )

    oidc_client = get_oidc_client(
        issuer=config['oidc']['issuer'],
        client_id=config['oidc']['client_id'],
        client_secret=config['oidc']['client_secret'],
        redirect_uri=config['oidc']['redirect_uri'],
    )

    '''
        redirect to idp to get access code
        if login successfully, rediret to /callback
    '''
    @app.route('/')
    def login():
        session['nonce'] = rndstr()
        session['state'] = rndstr()

        args = {
            "response_type": ['code'],
            "scope": ['openid', 'email', 'profile', 'offline_access'],
            "redirect_uri": config['oidc']['redirect_uri'],
            "nonce": session['nonce'],
            "state": session['state'],
        }

        auth_req = oidc_client.construct_AuthorizationRequest(request_args=args)
        login_url = auth_req.request(oidc_client.authorization_endpoint)

        return redirect(login_url)

    '''
        callback code to exchange token
        return command to configure kubeconfig
    '''
    @app.route('/callback')
    def callback():
        aresp = oidc_client.parse_response(
            AuthorizationResponse,
            info=request.query_string.decode('utf-8'),
            sformat="urlencoded"
        )

        assert aresp['state'] == session['state']

        args = {
            "code": aresp['code']
        }

        resp = oidc_client.do_access_token_request(
            state=aresp['state'],
            request_args=args,
            authn_method="client_secret_basic",
            client_secret=config['oidc']['client_secret'],
        )

        id_token = resp.raw_id_token
        user_email = resp['id_token']['email']
        refresh_token = resp['refresh_token']

        kubeconfig = yaml.dump(
            get_kubeconfig(
                ca=config['cluster']['ca'],
                host=config['cluster']['host'],
                name=config['cluster']['name'],
                user_email=user_email,
                client_id=config['oidc']['client_id'],
                client_secret=config['oidc']['client_secret'],
                id_token=id_token,
                issuer=config['oidc']['issuer'],
                refresh_token=refresh_token,
            ),
            default_flow_style=False,
        )

        response = make_response(response_format.format(kubeconfig), 200)
        response.mimetype = 'text/plain'
        return response

    @app.route('/ping')
    def ping():
        return '', 200

    return app
