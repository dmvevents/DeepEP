#pragma once

#include "configs.cuh"
#include "exception.cuh"
#include "utils.cuh"

namespace deep_ep {

/**
 * @brief Replacement for ibgda_get_p2p_ptr function to handle peer memory access
 *
 * AWS Optimization: Uses nvshmem_ptr for NVLink detection
 * - Returns valid pointer when NVLink available (p5.48xlarge instances)
 * - Returns 0 for EFA-only paths, triggering proper RDMA operations
 *
 * @param ptr The local memory pointer to translate
 * @param rank The current process rank
 * @param dst_rank The destination process rank
 * @return Translated peer-accessible pointer or 0 if not accessible
 */
__device__ __forceinline__ uint64_t nvshmemi_get_p2p_ptr(const uint64_t& ptr, const int& rank, const int& dst_rank) {
    if (rank == dst_rank)
        return ptr;

    // Use nvshmem_ptr to obtain the remote pointer
    // In EFA environment, this returns NULL; with NVLink, returns valid pointer
    void* remote_ptr = nvshmem_ptr(reinterpret_cast<void*>(ptr), dst_rank);
    if (remote_ptr == NULL)
        return 0;

    return reinterpret_cast<uint64_t>(remote_ptr);
}

/**
 * @brief Warp-collective non-blocking put operation
 *
 * AWS Optimization: Simplified warp-level interface
 * - Uses nvshmem_putmem_nbi for compatibility
 * - Can be replaced with nvshmemx_putmem_nbi_warp for higher performance
 *
 * @tparam kAlwaysDoPostSend Whether to always post send completion
 * @param req_rptr Remote destination address
 * @param req_lptr Local source address
 * @param bytes Number of bytes to transfer
 * @param dst_pe Destination processing element
 * @param qp_id Queue pair ID (unused, kept for API compatibility)
 * @param lane_id Warp lane ID
 * @param message_idx Message index for batched operations
 */
template <bool kAlwaysDoPostSend = false>
__device__ __forceinline__ void
nvshmemi_ibgda_put_nbi_warp(uint64_t req_rptr, uint64_t req_lptr, size_t bytes, int dst_pe, int qp_id, int lane_id, int message_idx) {
    if (lane_id == 0) {
        nvshmem_putmem_nbi(reinterpret_cast<void*>(req_rptr),
                          reinterpret_cast<const void*>(req_lptr),
                          bytes,
                          dst_pe);
    }
    __syncwarp();
}

/**
 * @brief Atomic add without fetch for batched signaling
 *
 * AWS Optimization: Batched signaling support
 * - Local operations use GPU atomics
 * - Remote operations use nvshmem_int_atomic_add
 *
 * @param rptr Pointer to target memory
 * @param value Value to add
 * @param pe Target processing element
 * @param qp_id Queue pair ID (unused, kept for API compatibility)
 * @param is_local_copy Flag indicating if operation is local
 */
__device__ __forceinline__ void
nvshmemi_ibgda_amo_nonfetch_add(void *rptr, const int& value, int pe, int qp_id, bool is_local_copy = false) {
    if (is_local_copy) {
        atomicAdd(static_cast<unsigned int*>(rptr), value);
    } else {
        nvshmem_int_atomic_add(static_cast<int*>(rptr), value, pe);
    }
}

/**
 * @brief Remote memory put operation
 */
__device__ __forceinline__ void
nvshmemi_ibgda_rma_p(void *rptr, const int& value, int pe, int qp_id) {
    nvshmem_int_p(static_cast<int*>(rptr), value, pe);
}

/**
 * @brief Quiet operation at phase boundaries
 *
 * AWS Optimization: Placed at strategic boundaries for batching
 * - Replaces per-QP quiet with global quiet
 * - Enables batching of multiple operations before synchronization
 */
__device__ __forceinline__ void
nvshmemi_ibgda_quiet(int dst_pe, int qp_id) {
    nvshmem_quiet();
}


} // namespace deep_ep