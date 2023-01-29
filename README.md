# kubeconfig-generator
kubectl authentication with identity provider using oidc.

config.yaml spec
```
flask_secret_key: # FLASK_SECRET_KEY
oidc:
  issuer: # IdP Issuer (e.g https://accounts.google.com)
  redirect_uri: # Callback URL (e.g https://my.domain.com/callback)
  client_id: # Client ID (created by IdP)
  client_secret: # Client Secret (created by IdP)
cluster:
  host: # api-server address (e.g 'https://my.domain.com:6443')
  ca: # base64 encoded certificate authority
  name: # cluster name (e.g cluster.local)
```

api-server argument
```
--oidc-client-id=<Your-Client-Secret>
--oidc-issuer-url=<IdP-Issuer>
--oidc-username-claim=<Claim> # e.g email
```
