/**
 * Copyright (c) 2018, NVIDIA CORPORATION. All rights reserved.
 * See file LICENSE for terms.
 */
 
#include <stdint.h>
#include <sys/socket.h>
#include <ucp/api/ucp.h>


ucp_listener_params_t c_util_get_ucp_listener_params(uint16_t port, ucp_listener_accept_callback_t callback_func, void *callback_args);

void c_util_get_ucp_listener_params_free(ucp_listener_params_t *param);

ucp_ep_params_t c_util_get_ucp_ep_params(const char *ip_address, uint16_t port);

void c_util_get_ucp_ep_params_free(ucp_ep_params_t *param);