#pragma once

#include "configs.cuh"
#include "exception.cuh"
#include "utils.cuh"

namespace deep_ep {

/**
 * @brief Replacement for ibgda_get_p2p_ptr function to handle peer memory access
 * 
 * Translates a local memory pointer to a peer-accessible pointer for direct memory access
 * between GPUs when available through NVSHMEM.
 * 
 * @param ptr The local memory pointer to translate
 * @param rank The current process rank
 * @param dst_rank The destination process rank
 * @return Translated peer-accessible pointer or 0 if not accessible
 */
__device__ __forceinline__ uint64_t nvshmemi_get_p2p_ptr(const uint64_t& ptr, const int& rank, const int& dst_rank) {
    // Local rank, no mapping required
    if (rank == dst_rank)
        return ptr;
    
    // Use nvshmem_ptr to obtain the remote pointer
    // Note: In an EFA environment, this may return NULL as EFA may not support direct memory access
    void* remote_ptr = nvshmem_ptr(reinterpret_cast<void*>(ptr), dst_rank);
    if (remote_ptr == NULL)
        return 0;
    
    return reinterpret_cast<uint64_t>(remote_ptr);
}

/**
 * @brief Replacement for nvshmemi_ibgda_put_nbi_warp to perform warp-collective non-blocking puts
 * 
 * Performs a non-blocking put operation using NVSHMEM primitives, coordinating
 * the transfer across a warp of threads for improved performance.
 * 
 * @tparam kAlwaysDoPostSend Whether to always post send completion
 * @param req_rptr Remote destination address
 * @param req_lptr Local source address
 * @param bytes Number of bytes to transfer
 * @param dst_pe Destination processing element
 * @param qp_id Queue pair ID
 * @param lane_id Warp lane ID
 * @param message_idx Message index for batched operations
 */
template <bool kAlwaysDoPostSend = false>
__device__ __forceinline__ void
nvshmemi_ibgda_put_nbi_warp(uint64_t req_rptr, uint64_t req_lptr, size_t bytes, int dst_pe, int qp_id, int lane_id, int message_idx) {
    // In EFA environment, we should use the standard nvshmem_putmem_nbi function
    // For warp-level operations, nvshmemx_uint64_put_nbi_warp could also be used
    if (lane_id == 0) {  // Only one thread performs the put operation
        nvshmem_putmem_nbi(reinterpret_cast<void*>(req_rptr),
                          reinterpret_cast<const void*>(req_lptr),
                          bytes,
                          dst_pe);
    }
    // Ensure all threads in the warp are synchronized
    __syncwarp();
}

/**
 * @brief Replacement for nvshmemi_ibgda_amo_nonfetch_add to perform atomic addition
 * 
 * Performs an atomic add operation without fetching the previous value.
 * Uses local atomics for local operations and NVSHMEM atomic operations for remote memory.
 *
 * @param rptr Pointer to target memory
 * @param value Value to add
 * @param pe Target processing element
 * @param qp_id Queue pair ID
 * @param is_local_copy Flag indicating if operation is local
 */
__device__ __forceinline__ void 
nvshmemi_ibgda_amo_nonfetch_add(void *rptr, const int& value, int pe, int qp_id, bool is_local_copy = false) {
    if (is_local_copy) {
        atomicAdd(static_cast<unsigned int*>(rptr), value);
    } else {
        // Use nvshmem_int_atomic_add for remote atomic operations
        nvshmem_int_atomic_add(static_cast<int*>(rptr), value, pe);
    }
}

} // namespace deep_ep