# Python Bindings for UCX

# Installing preliminary Conda packages

Some preliminary Conda packages can be installed as so. Replace `<CUDA
version>` with either `9.2`, `10.0`, or `10.1`. Also replace `<processor type>`
with `cpu` or `gpu`.

```
conda create -n ucx -c conda-forge -c jakirkham/label/ucx-new cudatoolkit=<CUDA version> ucx-proc=*=<processor type> ucx ucx-py python=3.7
```

The ucx recipe can be found here: https://github.com/conda-forge/ucx-split-feedstock/tree/f13e882cc0566e795ff12f2a039f490ce1653698/recipe

Note: These packages depend on the following system libraries being present:
`libibverbs`, `librdmacm`, and `libnuma` (`numactl` on Enterprise Linux). So
please install these with your Linux system's package manager.

# Build from source

The following instructions assume you'll be using `ucx-py` on a CUDA enabled system. The instructions assume you're using CUDA 9.2 for unspecific reasons. Change the `CUDA_HOME` environment variable, and the environment created and used by `conda` to `cudf_dev_10.0.yml` in order to support CUDA 10.

## Using Dask, Cudf, and UCX together ##

These three libraries provide a powerful combination of HPC message passing
tools. Using them involves using the correct dependencies, in the correct
order:

## NVIDIA repositories ##

### cudf ###

    git clone git@github.com:rapidsai/cudf.git
    cd cudf
    export CUDA_HOME=/usr/local/cuda-9.2
    export CUDACXX=$CUDA_HOME/bin/nvcc
    conda env create --name cudf_dev_92 --file conda/environments/cudf_dev_cuda9.2.yml
    conda activate cudf_dev_92
    ./build.sh
    cd ..

### dask ###

    git clone https://github.com/dask/dask.git
    cd dask
    pip install -e .
    cd ..

### dask distributed ###

    git clone https://github.com:dask/distributed.git
    cd distributed
    pip install -e .
    cd ..

### conda-forge Dependencies ###

    conda install -c conda-forge automake make cmake libtool pkg-config pytest-asyncio cupy distributed

### dask-cuda ###

    conda install -c rapidsai-nightly -c nvidia -c conda-forge dask-cuda

### UCX ###

    git clone https://github.com/openucx/ucx
    cd ucx
    ./autogen.sh
    mkdir build
    cd build
    ../configure --prefix=$CONDA_PREFIX --enable-debug --with-cuda=$CUDA_HOME --enable-mt CPPFLAGS="-I//$CUDA_HOME/include"
    make -j install

### ucx-py ###

    git clone git@github.com:rapidsai/ucx-py.git
    cd ucx-py
    python setup.py build_ext --inplace
    python -m pip install -e .

You should be done! Test the result of your build with

    pytest -v

### TCP Support

In order to use TCP add `tcp` to `UCX_TLS` and set `UCXPY_IFNAME` to the network interface you want to use. Some setup examples:

    # TCP using "eth0" and CUDA support
    export UCX_TLS=tcp,sockcm,cuda_copy,cuda_ipc
    export UCX_SOCKADDR_TLS_PRIORITY=sockcm
    export UCXPY_IFNAME="eth0"

    # InfiniBand using "ib0" and CUDA support
    export UCX_TLS=sockcm,cuda_copy,cuda_ipc
    export UCX_SOCKADDR_TLS_PRIORITY=sockcm
    export UCXPY_IFNAME="ib0"

    # TCP using "eno0" and no CUDA support
    export UCX_TLS=tcp,sockcm
    export UCX_SOCKADDR_TLS_PRIORITY=sockcm
    export UCXPY_IFNAME="eno0"

