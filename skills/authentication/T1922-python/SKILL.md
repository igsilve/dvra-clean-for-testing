---
name: use-secure-oauth-2-0-and-openid-connect-integration
description: Use dedicated OAuth 2.0/OIDC client integrations and validated token claims instead of manual callback or identity handling. Use when Python code manually processes OAuth/OIDC flows or trusts request-supplied identity data.
---

# Use secure OAuth 2.0 and OpenID Connect integration

## What This Skill Does
This skill fixes improper access control and insecure authentication flow handling in Python applications that integrate with OAuth 2.0 or OpenID Connect. It replaces manual authorization URL building, callback parsing, token handling, and identity extraction with a dedicated client integration such as Authlib, keeps provider configuration fixed on the server, and ensures identity and authorization decisions come only from validated token results and claims rather than raw request parameters.

## Decision Table
| Situation | Action |
|-----------|--------|
| Callback handlers read `request.args`, `request.GET`, `request.query_params`, `request.form`, or similar for `access_token`, `code`, `state`, `user`, `sub`, or `email` | Apply this fix |
| Python code manually handles OAuth/OIDC callback exchange instead of using a client library | Replace with a dedicated integration such as `authlib.integrations.*` and use `authorize_access_token()` |
| Code uses identity claims for login or profile data | Read claims only from the validated token result or `userinfo`, not directly from the request |
| Authorization checks use only token existence but do not compare `sub` or scopes to the requested resource | Add claim and scope checks before returning protected data |
| Code already uses a dedicated client integration, fixed provider config, and validated claims for identity and authorization | No action needed |

## Boundaries

### Can Do
- Replace manual OAuth/OIDC callback handling with a dedicated Python client integration
- Move identity parsing to validated token or `userinfo` results returned by the client library
- Add subject and scope checks so valid tokens cannot access unauthorized resources

### Cannot Do
- Choose or provision the correct identity provider, client registration, or provider-side policy
- Guarantee security if downstream code still trusts raw request data after callback validation
- Infer missing business authorization rules when the application does not define required scopes or ownership rules

## Gotchas
- Treating callback parameters as authenticated data: `code`, `state`, `access_token`, `user`, `sub`, and `email` in the request are attacker-controlled until the client integration validates them
- Using OIDC identity claims for authorization without scope or ownership checks: authentication data identifies the caller but does not by itself grant access to every resource
- Mixing manual JWT or ID token decoding with client-library flow handling: this bypasses built-in validation paths and often skips issuer, audience, nonce, or state checks

## Quick Verification
```bash
# Confirm a secure OAuth/OIDC client integration path exists
rg -n "authorize_access_token\(|create_client\(|from authlib\.integrations" .

# Find unguarded manual callback/identity handling from request input
rg -n "request\.(args|get_json|form|values|GET|POST|query_params).*(access_token|code|state|user|sub|email)|access_token\s*=\s*request\.|user(info)?\s*=\s*request\." .

# Find places that introspect or accept tokens but may skip subject/scope authorization checks
rg -n "introspect_token\(|Authorization|Bearer|scope|claims\.get\(\"sub\"\)|requested_user" .

# Generic Python build/test verification
python -m compileall .
python -m unittest discover
pytest -q
```

---

## Additional Requirements (SD Elements project)

These requirements apply to T1922 in this project because of its survey answers. Copied verbatim from SD Elements.

### Context information on OAuth 2.0 and OIDC

The era of standalone applications is long gone. Today, web and mobile applications use a set of APIs to fetch information about the user or to perform operations in the user's name. And in turn, many applications expose an API that other applications can use.

Such an interconnected world of applications and APIs raises many questions. How can the user allow an application to access a service on their behalf? Does the user need to share their credentials to give another application access? And what if the user wants to revoke access later on?

These questions are addressed by OAuth 2.0. With OAuth 2.0, a user can delegate access on their behalf to a client application. By using OAuth 2.0, the client can access an API  on behalf of the user, without the need to access the user's credentials. OAuth 2.0 also supports the concept of permissions, allowing the user to define what the application can do. We describe OAuth 2.0 in more detail in the Amendment section: 'The purpose of OAuth 2.0'.

OpenID Connect (OIDC) is an authentication protocol built on top of OAuth 2.0. Its purpose is to enable a federated identity mechanism through a centralized provider. The OpenID Provider will authenticate the end user, and provide the client application with proper authentication and identity information. The client application, in turn, can use this identity information to link the identity of the end user to the concept of a user within the application.

While OIDC is built on top of OAuth 2.0, they are typically used in a complementary fashion. OIDC is used to establish the identity of the user, while OAuth 2.0 mechanisms allow the client to access protected resources on resource servers. Even when the client only needs authentication, an OAuth 2.0-based mechanism can be used to retrieve additional user information from the "userinfo" endpoint. We describe OIDC in more detail in the Amendment section: 'The purpose of OIDC'.

### The purpose of OAuth 2.0

### The purpose of OAuth 2.0

The primary purpose of OAuth 2.0 is to allow a client application to access a protected resource on behalf of the user. A typical example of such a protected resource is an API. To access a protected resource, the client needs an access token. This access token represents the authority of the client. The resource server uses the access token to verify if the client is authorized to access the requested resource.

The OAuth 2.0 specifications describe various flows that allow different types of clients to obtain an access token. This amendment provides more details on the OAuth 2.0 terminology and the concepts behind the different flows.


### Terminology

One of the more confusing aspects of OAuth 2.0 is the terminology. The terms used in the specification are well-defined. The problem is that terms like a "client" mean something else to a web or mobile developer. To avoid any confusion, we will first set the record straight.

OAuth 2.0 is all about delegating access to applications on the user's behalf. Whether the user is delegating access to data, or operations, or something else does not matter. All of these items are referred to as a _**protected resource**_. 

These protected resources are hosted on a _**resource server**_. Typically, this is the API implementation exposing the data and operations. The resource server is responsible for verifying which client is accessing the API and whether the client is authorized to do so.

Protected resources are accessed by a _**client**_. A client can be a web application, a desktop application, a mobile application, or anything else. Note that the term client here merely refers to an entity wanting to access a protected resource. It does not imply that this needs to be a client-side application. 

Somebody needs to grant the client access to a protected resource. This role is fulfilled by the _**resource owner**_. In most cases, this will be the end user of the application. 

Finally, we have the central authority coordinating the whole process: the _**authorization server**_. The authorization server has several responsibilities: authenticating both the client and the user, and determining if the client is allowed to access the requested protected resources. The authorization server will issue an _**access token**_ to the client. The client uses this access token to contact the resource server to access protected resources.


### Client types

The OAuth 2.0 specification distinguishes between two types of clients: confidential clients and public clients. Confidential clients are considered to be capable of safeguarding a secret from external parties. One example of a confidential client is a backend web application. 

The second type is a public client. These are clients that are incapable of keeping a secret. Examples are frontend web applications that run in the browser of the user. Nothing stops a user from diving into the code and extracting secret information from the code. Similarly, mobile and native applications are considered to be public clients.

Public clients do not receive a client secret and are more constrained than confidential clients. Note that these restrictions are at the discretion of the authorization server. As a result, they may differ between implementations.


### Conceptual overview

To access an API on behalf of the user, the client needs to ask for the proper permissions first. OAuth 2.0 defines a couple of different flows to obtain such permission. In the end, they all result in the issuing of an access token. These flows are known as grant types and are mainly handled by the authorization server. Technically, the flows involve a few redirections and user interactions, details of which are covered below. 


The original OAuth 2.0 specification, along with a set of amendments, specifies a number of different flows to obtain an access token. Here, we discuss the flows that are considered to be a current best practice. 


#### The Client Credentials Grant

The client credentials flow is the most straightforward flow because it does not involve delegated access on behalf of the user. It allows a confidential client application to authenticate itself using the client ID and client secret. Doing so grants access to resources associated with this client, such as client-specific APIs. Think of the client credentials flow as server-to-server communication, with no direct human interaction.

More details on the Client Credentials flow are available in Amendment of [Task 1887](/library/tasks/T1887/): 'Understanding the Client Credentials flow'.


#### The Authorization Code Grant with PKCE

The authorization code grant flow supports delegated access to a client on behalf of the user. This flow is the current best practice for use in both public and confidential clients. 

More details on the Authorization Code flow with PKCE are available in Amendment of [Task 1887](/library/tasks/T1887/): 'Understanding the Authorization Code Grant flow with PKCE'.


#### The "Device Flow"

The device flow is a recent addition to the set of flows. This particular flow targets devices where the user cannot easily authenticate to the central authorization server. Examples are smart TVs or other input-constrained devices.

While the device flow supports a specific purpose, the details of the flow are not very complicated. Therefore, refer to [the spec](https://oauth.net/2/device-flow/) for more details.

### The purpose of OpenID Connect

### The purpose of OIDC

OAuth 2.0 provides a framework to allow a client application to access resources on behalf of the user. One example is the backend of a web application being able to access APIs on behalf of the user. With the rising popularity of OAuth 2.0, many people started finding ways to use OAuth 2.0 to obtain identity information about the user. With that identity information, the client can authenticate the user, hence establishing a form of federated identity.

There is, however, one significant problem with this approach. OAuth 2.0 by itself is not intended as an authentication framework. Instead, it is designed to offer delegated access to applications. While subtle, these properties make the plain OAuth 2.0 flows unsuited for authentication purposes. 

OIDC is a protocol built on top of OAuth 2.0. The OIDC protocol augments the plain OAuth 2.0 flows with properties to support proper end-user authentication. It also makes concrete decisions in places where OAuth 2.0 leaves the decision up to the developer. For example, the format of an identity token returned in an OIDC flow is a JWT with a reserved set of claims. Another example is the "userinfo" endpoint, which is a fixed endpoint where the client can retrieve additional information about the authenticated user.


### Terminology

While OIDC is built on top of OAuth 2.0, the specifications use slightly different terminology. The table below gives an overview of the differences, along with the simplified terminology we use in our guidelines.

| OAuth 2.0            | OIDC            | Guidelines        | Description |
| -------------------- | --------------- | ----------------- | ----------- |
| Client               | Relying Party   | Client            | The application requesting identity information, or requesting access to protected resources. |
| Authorization Server | OpenID Provider | Authorization server / Identity provider | The centralized service handling an OAuth 2.0 or OIDC flow. Responsibilities of this service include user authentication and client authorization. |
| Resource Owner       | End User        | User              | The end user delegating access or authenticating. This user is also responsible for authorizing the client application to access its information or resources. |



### Conceptual overview

Conceptually, OIDC is almost identical to OAuth 2.0. When using OIDC, the OAuth 2.0 flow is modified to return an **identity token**, which contains information about the user's authentication with the identity provider. We will highlight these changes in separate content items covering OIDC specifically.
