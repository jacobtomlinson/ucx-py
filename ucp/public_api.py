# Copyright (c) 2019, NVIDIA CORPORATION. All rights reserved.
# See file LICENSE for terms.

import gc
import os
import weakref

from . import exceptions
from ._libs import core

# The module should only instantiate one instance of the application context
# However, the init of CUDA must happen after all process forks thus we delay
# the instantiation of the application context to the first use of the API.
_ctx = None


def _get_ctx():
    global _ctx
    if _ctx is None:
        _ctx = core.ApplicationContext()
    return _ctx


# Here comes the public facing API.
# We could programmable extract the function definitions but
# since the API is small, it might be worth to explicit define
# the functions here.


def get_ucx_version():
    """Return the version of the underlying UCX installation

    Notice, this function doesn't initialize UCX.

    Returns
    -------
    tuple
        The version as a tuple e.g. (1, 7, 0)
    """
    return core.get_ucx_version()


def init(options={}, env_takes_precedence=False):
    """Initiate UCX.

    Usually this is done automatically at the first API call
    but this function makes it possible to set UCX options programmable.
    Alternatively, UCX options can be specified through environment variables.

    Parameters
    ----------
    options: dict, optional
        UCX options send to the underlying UCX library
    env_takes_precedence: bool, optional
        Whether environment variables takes precedence over the `options`
        specified here.
    """
    global _ctx
    if _ctx is not None:
        raise RuntimeError(
            "UCX is already initiated. Call reset() and init() "
            "in order to re-initate UCX with new options."
        )
    if env_takes_precedence:
        for k in os.environ.keys():
            if k in options:
                del options[k]

    _ctx = core.ApplicationContext(options)


def create_listener(callback_func, port=None):
    """Create and start a listener to accept incoming connections

    callback_func is the function or coroutine that takes one
    argument -- the Endpoint connected to the client.

    In order to call ucp.reset() inside callback_func remember to
    close the Endpoint given as an argument. It is not enough to

    Also notice, the listening is closed when the returned Listener
    goes out of scope thus remember to keep a reference to the object.

    Parameters
    ----------
    callback_func: function or coroutine
        a callback function that gets invoked when an incoming
        connection is accepted
    port: int, optional
        an unused port number for listening

    Returns
    -------
    Listener
        The new listener. When this object is deleted, the listening stops
    """
    return _get_ctx().create_listener(callback_func, port)


async def create_endpoint(ip_address, port):
    """Create a new endpoint to a server

    Parameters
    ----------
    ip_address: str
        IP address of the server the endpoint should connect to
    port: int
        IP address of the server the endpoint should connect to

    Returns
    -------
    _Endpoint
        The new endpoint
    """
    return await _get_ctx().create_endpoint(ip_address, port)


def progress():
    """Try to progress the communication layer

    Returns
    -------
    bool
        Returns True if progress was made
    """
    return _get_ctx().progress()


def get_ucp_worker():
    """Returns the underlying UCP worker handle (ucp_worker_h)
    as a Python integer.
    """
    return _get_ctx().get_ucp_worker()


def get_config():
    """Returns all UCX configuration options as a dict.

    If UCX is initialized, the options returned are the
    options used if UCX were to be initialized now.
    Notice, this function doesn't initialize UCX.

    Returns
    -------
    dict
        The current UCX configuration options
    """

    if _ctx is None:
        return core.get_config()
    else:
        return _get_ctx().get_config()


def reset():
    """Resets the UCX library by shutting down all of UCX.

    The library is initiated at next API call.
    """
    global _ctx
    if _ctx is not None:
        _ctx.unbind_epoll_fd_to_event_loop()
        weakref_ctx = weakref.ref(_ctx)
        _ctx = None
        gc.collect()
        if weakref_ctx() is not None:
            msg = (
                "Trying to reset UCX but not all Endpoints and/or Listeners "
                "are closed(). The following objects are still referencing "
                "ApplicationContext: "
            )
            for o in gc.get_referrers(weakref_ctx()):
                msg += "\n  %s" % o
            raise exceptions.UCXError(msg)


class Listener:
    """A handle to the listening service started by `create_listener()`

    The listening continues as long as this object exist or `.close()` is called.
    Please use `create_listener()` to create an Listener.
    """

    def __init__(self, backend):
        self._b = backend
        self._closed = False

    def __del__(self):
        if not self.closed():
            self.close()

    def closed(self):
        """Is the listener closed?"""
        return self._closed

    @property
    def port(self):
        """The network point listening on"""
        return self._b.port()

    def close(self):
        """Closing the listener"""
        if not self._closed:
            self._b.destroy()
            self._closed = True
            self._b = None


class Endpoint:
    """An endpoint represents a connection to a peer

    Please use `create_listener()` and `create_endpoint()`
    to create an Endpoint.
    """

    def __init__(self, ep):
        self._ep = ep

    def __del__(self):
        if not self.closed():
            self.close()

    @property
    def uid(self):
        """The unique ID of the underlying UCX endpoint"""
        return self._ep.uid

    async def signal_shutdown(self):
        """Signal the connected peer to shutdown.

        Notice, this functions doesn't close the endpoint.
        To do that, use `Endpoint.close()` or del the object.
        """
        await self._ep.signal_shutdown()

    def closed(self):
        """Is this endpoint closed?"""
        return self._ep._closed

    def close(self):
        """Close this endpoint.

        Notice, this functions doesn't signal the connected peer to shutdown
        To do that, use `Endpoint.signal_shutdown()`
        """
        return self._ep.close()

    async def send(self, buffer, nbytes=None):
        """Send `buffer` to connected peer.

        Parameters
        ----------
        buffer: exposing the buffer protocol or array/cuda interface
            The buffer to send. Raise ValueError if buffer is smaller
            than nbytes.
        nbytes: int, optional
            Number of bytes to send. Default is the whole buffer.
        """
        await self._ep.send(buffer, nbytes=nbytes)

    async def recv(self, buffer, nbytes=None):
        """Receive from connected peer into `buffer`.

        Parameters
        ----------
        buffer: exposing the buffer protocol or array/cuda interface
            The buffer to receive into. Raise ValueError if buffer
            is smaller than nbytes or read-only.
        nbytes: int, optional
            Number of bytes to receive. Default is the whole buffer.
        """
        await self._ep.recv(buffer, nbytes=nbytes)

    def ucx_info(self):
        """Return low-level UCX info about this endpoint as a string"""
        return self._ep.ucx_info()

    def cuda_support(self):
        """Return whether UCX is configured with CUDA support or not"""
        return self._ep._cuda_support

    def get_ucp_worker(self):
        """Returns the underlying UCP worker handle (ucp_worker_h)
        as a Python integer.
        """
        return self._ep.get_ucp_worker()

    def get_ucp_endpoint(self):
        """Returns the underlying UCP endpoint handle (ucp_ep_h)
        as a Python integer.
        """
        return self._ep.get_ucp_endpoint()
