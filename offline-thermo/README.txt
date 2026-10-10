Offline validation dependencies for Windows x64 / Python 3.11.
NumPy and SciPy are already required by the existing project validation tools and are not included.
Install from the repository root:
.\.venv\Scripts\python.exe -m pip install --no-index --find-links .\offline-thermo thermo==0.6.0 chemicals==1.5.0 fluids==1.3.0 pandas==2.2.3
Then run tools\benchmark_web_cmu.py.
Files downloaded using pip from the configured package index; SHA256SUMS records local artifact hashes.
