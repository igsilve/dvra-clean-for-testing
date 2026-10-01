---
name: decide-on-the-right-oauth-2-0-flow-for-your-application
description: "Select and enforce safe OAuth 2.0 flows in Python to prevent improper authorization; Use when flow choice, PKCE, client authentication, refresh token use, or grant construction is derived from config, input, or inconsistent logic."
---

# Decide on the right OAuth 2.0 flow for your application

## What This Skill Does
This skill fixes improper authorization caused by selecting unsafe or inconsistent OAuth 2.0 flows in Python. It replaces ad hoc flow selection with one deterministic selector, rejects unsupported flows such as Implicit Grant, requires PKCE with S256 for Authorization Code, restricts client authentication to confidential clients only, blocks refresh token use for browser-based clients, and ensures each token request uses only the exact grant fields allowed for the selected flow.

## Decision Table
| Situation | Action |
|-----------|--------|
| OAuth flow is chosen from config strings, request parameters, or scattered endpoint logic | Add a single `select_oauth_flow(...)` function with an allowlist of `authorization_code_pkce`, `device_flow`, and `client_credentials`; reject anything else |
| End-user client is web, desktop, or mobile and is not a constrained-input device | Use Authorization Code with PKCE and require `code_challenge`, `code_challenge_method="S256"`, and `code_verifier` |
| Public client is browser-based, mobile, or otherwise cannot keep secrets | Do not send `client_secret` or private-key client auth; reject public-client token requests that include secret-based authentication |
| Constrained-input public client needs user authorization | Use Device Flow and require `device_code`; do not fall back to Implicit Grant |
| Code already derives flow from explicit client traits, enforces PKCE, forbids public-client secrets, and gates refresh tokens consistently | No action needed |

## Boundaries

### Can Do
- Centralize OAuth flow selection in a deterministic Python function or policy module
- Enforce PKCE with S256 for Authorization Code flows at authorization and token exchange time
- Split confidential-client and public-client token request construction and reject invalid grant payloads

### Cannot Do
- Prove the identity provider is configured securely server-side if the application never validates its own requests
- Invent secure storage for refresh tokens where the platform cannot protect them
- Determine business authorization scopes or user entitlements beyond enforcing safe flow and grant usage

## Gotchas
- Treating browser or mobile apps as confidential clients: client secrets on end-user devices are exposed and must not be relied on
- Adding PKCE only to the authorization request: token exchange must also require and send the matching `code_verifier`
- Allowing `grant_type` or flow names from runtime input: this reintroduces unsafe flows such as `implicit` or mixed grant payloads

## Quick Verification
```bash
# Confirm the secure selector / guards exist
rg -n "select_oauth_flow|ALLOWED_FLOWS|authorization_code_pkce|device_flow|client_credentials|may_use_refresh_tokens|build_grant_payload|code_challenge_method[\"']?\s*[:=]\s*[\"']S256[\"']" .

# Find unguarded or unsafe OAuth usage that may bypass the fix
rg -n "implicit|response_type[\"']?\s*[:=]\s*[\"']token[\"']|grant_type[\"']?\s*[:=]\s*[\"']implicit[\"']|client_secret\s*=|HTTPBasicAuth\(|grant_type[\"']?\s*[:=]\s*[\"']authorization_code[\"']" .

# Basic Python build check for syntax across app, library, CLI, or service code
python -m compileall .

# Run tests if present
python -m unittest discover -v
```

---

## Additional Requirements (SD Elements project)

These requirements apply to T1887 in this project because of its survey answers. Copied verbatim from SD Elements.

### Purpose of each OAuth 2.0 flow

Each OAuth 2.0 flow serves a specific purpose. Below, we illustrate these purposes using a client application suite for an imaginary SocialNetwork. The clients offer the following features:

* A client displaying a live feed of a timeline in a browser
    * This client requires involvement of the end-user
    * This is a frontend web application, without server-side component (i.e., a public client)
* A client displaying a live feed of a timeline on a smart TV
    * This client requires involvement of the end-user
    * This is a native frontend application, without server-side component (i.e., a public client)
* A client that offers a UI allowing the users to schedule posts to their timeline ahead of time
    * This client requires involvement of the end-user
    * This is a full stack web application (i.e., a confidential client)
* A client that retrieves logging information from the SocialNetwork for security purposes
    * This client does not require involvement of the end-user
    * This is a native application running on a server (i.e., a confidential client)


#### Client Credentials flow

In our SocialNetwork scenario, there is a dedicated client application to retrieve logging information from the SocialNetwork. It can retrieve all logging events associated with the different set of clients from this developer. Granting access to those logs is the responsibility of the SocialNetwork. 

Note how this type of access does not require the involvement of the end user. There is no action to be performed on behalf of the user. The client can access the logs directly after having authenticated itself to the SocialNetwork. 

In essence, you can view the Client Credentials Grant as a flow to enable authenticated machine-to-machine communication. The Client Credentials flow allows a client to authenticate itself and receive an access token to access its protected resources. Since the Client Credentials flow depends on the use of the client secret, it can only be used with confidential clients.


#### Authorization Code flow with PKCE

The Authorization Code flow with PKCE is targeted towards clients that need to act on behalf of the user. With the recent addition of *Proof Key for Code Exchange (PKCE)*, this flow is both suited for public and confidential clients. In our SocialNetwork scenario, these clients can both use this flow:

* A client displaying a live feed of a timeline in a browser
* A client that offers a UI allowing the users to schedule posts to their timeline ahead of time

Note that the type of client influences the security considerations for these flows. We already discussed these briefly earlier in this task, and go into more detail in the Amendment.


#### Device flow

Since the introduction of OAuth 2.0, the client landscape has changed significantly. Today, users sign in to applications from smart TVs, game consoles, and streaming devices.

When the authorization server needs the user to authenticate, the user will need to enter credentials, along with a potential second factor. Doing so on a device with constrained input provides bad user experience, or is even impossible when no browser is present.

The recently added device flow explicitly supports browserless and input constrained devices. The specification proposes a user-friendly way to enable clients running on such a device to run a proper OAuth 2.0 flow, by offloading the authentication to a regular device.

Refer to the [specification](https://oauth.net/2/device-flow/) for more details.

### Understanding the Authorization Code Grant flow with PKCE

In this amendment, we provide details on the _**Authorization Code flow with PKCE**_. We provide two scenarios: one for confidential clients and one for public clients. Implementation details can be found in How-to section 'Implementing the Authorization Code Grant flow with PKCE'.

### Overview of the flow

This amendment gives a high-level overview of the Authorization Code flow with PKCE, as shown in the scenario. In contrast to the Authorization Code Grant flow, the client is a native client-side application. The user's browser is also depicted, as it still plays a crucial role in the delegation process. 

![](https://staging.qa.sdelements.com/static/screenshots/TA1015_OAuth_2_Confidential_Client.png)

The flow is initialized by the client application, which is the backend of the full-stack application (Step 1). To direct the flow to the authorization server, the application instructs the browser to follow a redirect. 

The client informs the authorization server it is running an Authorization Code Grant flow (Step 2). It provides the necessary information in the initial URI using query parameters. One of these parameters is a _**code challenge**_. This code challenge is used to ensure that only this client can use the issued authorization code to request an access token. We will cover the details of the parameters, as well as the code challenge, in ['Implementing the Authorization Code Grant flow with PKCE'](TODO-REF-HOWTO) How-to .

When handling the request, the authorization server is supposed to authenticate the resource owner, and request permission to delegate access to the client application. (Step 3 and 4). After successful completion of these steps, the authorization server issues an authorization code. 

This authorization code is sent back to the user's browser (Step 5). To do so, the authorization server constructs a redirect URI, pointing back to the client application. The user agent loads this redirect URI, which transmits the necessary information to the client application (Step 6). 

The client application now needs to exchange the authorization code for an access token. To perform the exchange, the client makes a backchannel request to the authorization server (Step 7). In the request, the client includes the authorization code, its client credentials, and the code verifier. This verifier is uniquely linked to the code challenge from before.

The authorization server, in turn, checks if the client credentials are valid and if the authorization code belongs to this particular client (step 8). The authorization server also checks if the code challenge from earlier matches the code verifier presented here. If everything checks out, it generates an access token for the client and sends it to the client in the response (step 9).

The decision to issue a refresh token to the client is at the discretion of the authorization server. If desired, the authorization server can issue a refresh token in the same response alongside the access token.


### The Authorization Code flow with PKCE for public clients

Here, you can find an overview of the Authorization Code flow with PKCE for public clients. The client is a frontend browser application, incapable of keeping a secret. Note that the flow itself remains mostly unchanged. 

The main difference is that the flow is not initialized from the browser application, instead of from the backend application. To differentiate between the client application and the browser, they are displayed separately in the diagram.

![](https://staging.qa.sdelements.com/static/screenshots/TA1015_OAuth_2_Public_Client.png)

We will not cover each step of the flow again. Instead, we highlight the differences:

* The flow starts directly in the browser, instead of in the backend of the application (step 1).
* The code challenge and verifier are handled by the frontend application.
* When loading the callback, the browser will make a request to a server to load the HTML page of the client (step 6). This request is not depicted here.
* The frontend application exchanges the authorization code for an access token (step 7).
* The code exchange does not use client credentials (step 7).

### Understanding the Client Credentials flow

This amendment provides details on the _**Client Credentials flow**_. This flow allows a client to authenticate itself to the authorization server to receive an access token. The client credentials flow is typically used to enable *machine-to-machine* communication.


### Overview of the flow

The Client Credentials flow is used when the client needs to access protected resources directly. As the scenario shows, there is no need for delegation on behalf of the user, hence no need to involve the end user in the flow. 

![](https://staging.qa.sdelements.com/static/screenshots/TA1016_OAuth_2_Client_Credentials_Flow.png)

The scenario of the Client Credentials flow aptly reflects its simplicity. The client reaches out to the token endpoint of the authorization server to request an access token (Step 1). It authenticates itself, typically by including client credentials.

The authorization server is responsible for authenticating the client. Next, it issues a response containing an access token (Step 2). With this access token, the client can access its protected resources by contacting the resource server.


### Relevant considerations

The most significant limitation of the Client Credentials flow is its intended purpose. This flow is intended to give a client access to its own resources. As a result, it cannot be used to delegate access to a client on behalf of the user.

However, the Client Credentials flow is useful to implement proper server-to-server authentication and authorization. Since it fits within the OAuth 2.0 framework, it provides the proper structure to register clients and manage client secrets (See Amendment section 'Securing client registration' under [Task 1889](/library/tasks/T1889/) for more details). Additionally, it enables the use of a single authorization mechanism to protect APIs for various types of access.

Finally, the authorization server does not issue refresh tokens during the Client Credentials flow. Refresh tokens allow a client to obtain previously authorized access tokens without involving the end user. Since the client can directly request access tokens with the Client Credentials flow, there is no need for refresh tokens.
