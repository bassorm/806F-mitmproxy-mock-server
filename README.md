## Mitmproxy: Mock Server

#### *Introduction*
This project contains a custom script and supporting files to configure [mitmproxy](https://mitmproxy.org/) as a mock server to greatly assist / speed up the software development process (it can be configured as a lot of other things too, but this is perhaps one of the most common usages of it as a development tool.)

#### *Goals*
- *Convenience/Speed*

  - It is intended to help scenarios during development (feature work, bug exploration, UI testing under certain use cases or edge cases, etc.) where it can be difficult or just inconvenient to receive real data of interest from some API directly (a test account is not set up with some specific state one needs, getting response data needed takes too much time to set up or search for manually, etc.).

- *Flexibility*

  - From a client perspective, it doesn't know or care *how* data is provided (from a "real" source or in this case, fed from the local file system) - as long as the response conforms to the expected schema/structure it needs, it will function just as if it received real data from the API.

- *Faster iteration*

  - This program and script should greatly speed up the iteration process - instead of manually changing actual code just to temporarily induce certain flows or edge cases of interest, the same behavior can be achieved by simply delegating it to the API layer (feed it substitute data from the local file system instead, via `mitmproxy` and this script).

- *Parallel development (remove dependency on backend)*
  - This server can also be used in scenarios where an API is *not even built yet* but you want to be able to start writing client code against a future implementation on backend side (based on some agreed API contract/schema up front).  This allows backend and frontend to work in parallel without being dependent on each other!

#### *Project Structure*

The overall functionality is organized according to the following files under the `matcher` folder:

- `main.py`: the main script that mitmproxy is run with to provide mock-server capability.  Run `mitmproxy` on command line from this repo root directory as follows:

  - `mitmproxy -s main.py`

- `matcher.json`: This is the list of request/response pairs of interest you want the mock server to match against (of course, any request *not* in this list or not matched against properly will still be forwarded to the real server as normal).  Each item contains the following key-value pairs:

  - `"method"`: The HTTP/S method type of the request (GET, POST, PATCH, etc.)

  - `"urlRegex"`: The base URL, including any optional path or endpoint info as necessary so the server can uniquely distinguish it from others to match against (allows for regular expressions as well - use `^` to denote start of `http(s)` request and `*` to match more flexibly against certain variants of path/endpoint values, etc.)

  - `"mockResponsePath"`: This is the path to the local file name (relative to the root of this repo clone) containing some desired response for a given request (for any match found, the mock server will feed the client with the info here instead of fetching the real response from the actual API server).  The `matcher.json` file  is currently set up to searche for all mock responses underneath the `matcher/mockResponses*` folder (but this could be changed to another name or path, as long as the script can still find it).

  - `"enabled:`: This parameter is here as a convenience to either enable or disable matching against a given request - instead of having to constantly delete and re-copy items inside the `matcher.json` file, one can simply toggle these on and off with this field (if value is `true`, the server will skip the real API response and provide the corresponding response from the local file system - if `false`, the server forwards the request to the real API to get an actual response)

- `mockResponses/*`: The directory containing all the mock responses for any requests listed inside `matcher.json` (can be changed as long as the script can still find the files).  Each mock response has the following configurable properties:
  - `"code"`: The HTTP/S code you want to return (instead of maybe what the real API would give)
  - `"headers"`: What headers you want the mock response to contain
  - `"delayMillis"`: This is a cool one - represents how long mitmproxy will purposely wait to return a mock response.  There are times when you want to arbitrarily create a "delay" in how long a "response" comes back from the "server".  Leverage this property to achieve this (unit is in milliseconds).  Benefits include:
    - If set to zero, it'll return responses immediately (no more waiting for server to take long to "process" a freqently slow request)
    - If set to a nonzero value, it can make it easier to verify that certain UI effects like loading spinners appear as expected (relying on real API responses makes this tricky because if a response comes back too quickly, there's not enough time to see what it looks actually like when active).
    - A nonzero value can also be used verify your client handles timeout errors gracefully (ex. in Java, `SocketTimeoutException`).  This can be awkward to test on a real API because a real response could come back too quickly.  Use a value greater than your network-config timeouts to simulate the "server" taking too long and your app closing the connection (and how your client responds to that).
    - Any super specific value (maybe you need a very specific time like 528ms to test a really hard-to-reproduce edge case)
  - `"body"`: The payload format you're expecting for that response that the client will consume in code (refer to your API docs).  This could be some JSON payload, an HTML response, etc.

#### *Notes*
- Your development client must be set up to accept the certificate of your `mitmproxy` installation.  See their website for how to configure it.
- Anytime a change is made to the `matcher.json` file, you must kill this server instance and restart it.  This is because the behavior for which requests to match against is read only once upon this script's startup (also, as a way to avoid spamming the file system since the `matcher.json` file would otherwise be constantly closed and reopened on every single request `mitmproxy` intercepts.)
- Changes to sample responses under `mockResponses` directory do *not* need the program to be killed and restarted (this is because these files are loaded on demand as they are needed, which is much less frequently than `matcher.json` would need if it followed the same idea.).  Simply edit the response of interest, and save the file before triggering that response again in the client app (and the data will be fed in real time the next time it is requested by the client).  This design avoids the problem of having to recompile the app code itself every time one temporarily changes it just to trigger certain flows.
- Make sure any VPNs on your device are turned *off* (any encrypted traffic on your device cannot be inspected by `mitmproxy` if it's already hidden by this)
- This script and `mitmproxy` only works on non-release builds typically (if your client app is not a debug build or does not accept user certificates, `mitmproxy` cannot intercept any requests from it because the client app doesn't trust it - you'll usually see error messages about this in `mitmproxy`'s log output)
- You need to set up your Wi-Fi or other connection on the test device to go through manual proxy settings instead (`mitmproxy` usually starts at port `8080` on the device running the server instance - set you network config on the client device to route traffic through it)

# Disclaimers

- Use this script and `mitmproxy` program for legitimate purposes only.  They are meant as tools to assist only in normal app development (for non-release builds to speed up progress) or for academic / personal learning.  Neither this script, nor the program itself, is intended to be abused by anyone to subvert production APIs (for any material gain or to cause injury to businesses) that would otherwise not allow those operations to be performed. 
- From a user/customer perspective, be careful when trusting "certificates" or "certificate authorities" in general.
- Also be careful in development when considering what certificates to enable or disable when releasing your product in production (debug/development builds are okay for testing, but consider carefully how production builds should behave before deployment).
- `mitmproxy` is actually its own Certificate Authority, but it will *not* work for client apps that do not enable trusting what are called "user certficates" (that is, certficates the user manually adds to their phone or device to allow `mitmproxy` to decrypt/re-encrypt traffic).  If you notice you're not getting responses from your local file system you expect but real responses still, check the logs in the program and that the app has been properly set up to trust the certificate of your `mitmproxy`'s installation instance already.

  - More info about how it works can be found on their [website](https://docs.mitmproxy.org/stable/concepts-howmitmproxyworks/#the-mitm-in-mitmproxy)

