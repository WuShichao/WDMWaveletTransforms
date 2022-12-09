"""helper functions for transform_time.py"""
import numpy as np
from numba import njit
from transform_freq_funcs import phitilde_vec
import fft_funcs as fft

@njit()
def assign_wdata(i,K,ND,Nf,wdata,data,phi):
    """assign wdata to be fftd in loop"""
    half_K = np.int64(K/2)
    for j in range(0,K):
        jj = i*Nf-half_K+j
        if jj<0:
            jj += ND  # periodically wrap the data
        if jj>=ND:
            jj -= ND # periodically wrap the data
        wdata[j] = data[jj]*phi[j]  # apply the window

#https://gitlab.com/gwburst/public/library/-/blob/public/wat/WDM.cc has inverse wavelet time transform
#   #see https://iopscience.iop.org/article/10.1088/1742-6596/363/1/012032/pdf

@njit()
def pack_wave(i,mult,Nf,wdata_trans,wave):
    """pack fftd wdata into wave array"""
    #wave[i,0] = np.sqrt(2.0)*np.real(wdata_trans[0])
    if i%2==0 and i<wave.shape[0]-1:
        #m=0 value at even Nt and
        wave[i,0] = np.real(wdata_trans[0])/np.sqrt(2)
        wave[i+1,0] = np.real(wdata_trans[Nf*mult])/np.sqrt(2)

    for j in range(1,Nf):
        if (i+j)%2:
            wave[i,j] = -np.imag(wdata_trans[j*mult])
        else:
            wave[i,j] = np.real(wdata_trans[j*mult])

def phi_vec(Nf,dt,nx=4.,mult=16):
    """get time domain phi as fourier transform of phitilde_vec"""
    #TODO fix mult

    DT = dt*Nf           # width of wavelet pixel in time
    DF = 1/(2*dt*Nf) # width of wavelet pixel in frequency
    OM = np.pi/dt
    #M = Nf
    L = 2*Nf
    DOM = OM/Nf
    insDOM = 1./np.sqrt(DOM)
    B = OM/L
    A = (DOM-B)/2.
    K = mult*2*Nf
    half_K = np.int64(K/2)

    Tw = dt*K

    #print("filter length = %d"%K)
    #print("Pixel size DT (seconds) %e DF (Hz) %e"%(DT, DF))
    #print("Filter length (seconds) %e full filter bandwidth %e"%(Tw, (A+B)/np.pi))

    dom = 2*np.pi/Tw  # max frequency is K/2*dom = pi/dt = OM

    DX = np.zeros(K,dtype=np.complex128)

    #zero frequency
    DX[0] =  insDOM

    DX = DX.copy()
    # postive frequencies
    DX[1:half_K+1] = phitilde_vec(dom*np.arange(1,half_K+1),Nf,dt,nx)
    # negative frequencies
    DX[half_K+1:] = phitilde_vec(-dom*np.arange(half_K-1,0,-1),Nf,dt,nx)
    DX = K*fft.ifft(DX,K)

    phi = np.zeros(K)
    phi[0:half_K] = np.real(DX[half_K:K])
    phi[half_K:] = np.real(DX[0:half_K])

    nrm = np.sqrt(K/dom)#*np.linalg.norm(phi)

    fac = np.sqrt(2.0)/nrm
    phi *= fac
    return phi


def transform_wavelet_time(data,Nf,Nt,ts,nx=4.,mult=32):
    """do the wavelet transform in the time domain"""
    # the time domain data stream
    ND = ts.size

    dt = ts[1]-ts[0]

    #TODO fix mult, can cause bad leakage if it is too small but may be possible to mitigate
    #mult = 16 # Filter is mult times pixel with in time

    #print("%d %d %d"%(ND, Nf, Nt))

    K = mult*2*Nf

    # windowed data packets
    wdata = np.zeros(K)

    wave = np.zeros((Nt,Nf))  # wavelet wavepacket transform of the signal
    phi = phi_vec(Nf,dt,nx,mult)

    for i in range(0,Nt):
        assign_wdata(i,K,ND,Nf,wdata,data,phi)
        wdata_trans = fft.rfft(wdata,K) #TODO check
        pack_wave(i,mult,Nf,wdata_trans,wave)

    return wave