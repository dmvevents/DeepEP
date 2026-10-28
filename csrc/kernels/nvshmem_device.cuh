#pragma once

#include "configs.cuh"
#include "exception.cuh"
#include "utils.cuh"

namespace deep_ep {

/**
 * @brief NVSHMEM-API replacement for nvshmemi_get_p2p_ptr in ibgda_device.cuh
 *
 * Returns a load/store address for dst_rank's copy of ptr, or 0 if there is none:
 * - dst_rank == rank: ptr itself
 * - a peer this GPU can load/store, such as a same-node GPU over NVLink on P5:
 *   the address nvshmem_ptr() maps
 * - any other peer, such as a GPU on another node: 0, and the caller uses an
 *   NVSHMEM put or atomic instead
 *
 * @param ptr The local memory pointer to translate
 * @param rank The current process rank
 * @param dst_rank The destination process rank
 * @return Translated peer-accessible pointer or 0 if not accessible
 */
__device__ __forceinline__ uint64_t nvshmemi_get_p2p_ptr(const uint64_t& ptr, const int& rank, const int& dst_rank) {
    if (rank == dst_rank)
        return ptr;

    // nvshmem_ptr() returns NULL when dst_rank's memory is not load/store accessible
    void* remote_ptr = nvshmem_ptr(reinterpret_cast<void*>(ptr), dst_rank);
    if (remote_ptr == NULL)
        return 0;

    return reinterpret_cast<uint64_t>(remote_ptr);
}

/**
 * @brief NVSHMEM-API replacement for the IBGDA warp put, called by a whole warp
 *
 * Lane 0 issues one nvshmem_putmem_nbi() for the whole message; the warp then
 * synchronizes with __syncwarp(). The put itself is not warp-collective.
 *
 * @tparam kAlwaysDoPostSend Unused, kept for API compatibility
 * @param req_rptr Remote destination address
 * @param req_lptr Local source address
 * @param bytes Number of bytes to transfer
 * @param dst_pe Destination processing element
 * @param qp_id Queue pair ID (unused, kept for API compatibility)
 * @param lane_id Warp lane ID; lane 0 issues the put
 * @param message_idx Unused, kept for API compatibility
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
 * @brief NVSHMEM-API replacement for the IBGDA non-fetching atomic add
 *
 * - is_local_copy: CUDA atomicAdd on the local address
 * - otherwise: nvshmem_int_atomic_add() to PE pe
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
 * @brief Single-int remote put via nvshmem_int_p(); qp_id is unused
 */
__device__ __forceinline__ void
nvshmemi_ibgda_rma_p(void *rptr, const int& value, int pe, int qp_id) {
    nvshmem_int_p(static_cast<int*>(rptr), value, pe);
}

/**
 * @brief NVSHMEM-API replacement for the IBGDA per-QP quiet
 *
 * Calls the global nvshmem_quiet(); dst_pe and qp_id are unused.
 */
__device__ __forceinline__ void
nvshmemi_ibgda_quiet(int dst_pe, int qp_id) {
    nvshmem_quiet();
}


} // namespace deep_ep