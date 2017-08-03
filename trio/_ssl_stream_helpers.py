import trio

from ._open_tcp_stream import DEFAULT_DELAY

__all__ = ["open_ssl_over_tcp_stream"]

# It might have been nice to take a ssl_protocols= argument here to set up
# NPN/ALPN, but to do this we have to mutate the context object, which is OK
# if it's one we created, but not OK if it's one that was passed in... and
# the one major protocol using NPN/ALPN is HTTP/2, which mandates that you use
# a specially configured SSLContext anyway! I also thought maybe we could copy
# the given SSLContext and then mutate the copy, but it's no good:
# copy.copy(SSLContext) seems to succeed, but the state is not transferred!
# For example, with CPython 3.5, we have:
#   ctx = ssl.create_default_context()
#   assert ctx.check_hostname == True
#   assert copy.copy(ctx).check_hostname == False
# So... let's punt on that for now. Hopefully we'll be getting a new Python
# TLS API soon and can revisit this then.
async def open_ssl_over_tcp_stream(
        host,
        port,
        *,
        https_compatible=False,
        ssl_context=None,
        # No trailing comma b/c bpo-9232 (fixed in py36)
        happy_eyeballs_delay=DEFAULT_DELAY
    ):
    """Make a TLS-encrypted Connection to the given host and port over TCP.

    This is a convenience wrapper that calls :func:`open_tcp_stream` and
    wraps the result in an :class:`~trio.ssl.SSLStream`.

    This function does not perform the TLS handshake; you can do it
    manually by calling :meth:`~trio.ssl.SSLStream.do_handshake`, or else
    it will be performed automatically the first time you send or receive
    data.

    Args:
      host (bytes or str): The host to connect to. We require the server
          to have a TLS certificate valid for this hostname.
      port (int): The port to connect to.
      https_compatible (bool): Set this to True if you're connecting to a web
          server. See :class:`~trio.ssl.SSLStream` for details. Default:
          False.
      ssl_context (:class:`~ssl.SSLContext` or None): The SSL context to
          use. If None (the default), :func:`ssl.create_default_context`
          will be called to create a context.
      happy_eyeballs_delay (float): See :func:`open_tcp_stream`.

    Returns:
      trio.ssl.SSLStream: the encrypted connection to the server.

    """
    tcp_stream = await trio.open_tcp_stream(
        host, port, happy_eyeballs_delay=happy_eyeballs_delay,
    )
    if ssl_context is None:
        ssl_context = trio.ssl.create_default_context()
    return trio.ssl.SSLStream(
        tcp_stream,
        ssl_context,
        server_hostname=host,
        https_compatible=https_compatible,
    )