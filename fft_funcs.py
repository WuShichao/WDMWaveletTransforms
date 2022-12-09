"""helper to make sure available fft functions are consistent across modules depending on install"""
try:
    import mkl_fft
    rfft = mkl_fft.rfft_numpy
    irfft = mkl_fft.irfft_numpy
    fft = mkl_fft.fft
    ifft = mkl_fft.ifft
except ImportError:
    print('mkl fft not available trying numpy')
    import numpy
    rfft = numpy.rfft
    irfft = numpy.irfft
    fft = numpy.fft
    ifft = numpy.ifft