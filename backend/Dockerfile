FROM python:3.14.2

WORKDIR /app


# Dependencies
RUN  apt-get update && \
     # Basic utilities
     apt-get -y install nano procps sqlite3 graphviz && \
     # LaTeX fonts
     apt-get -y install texlive texlive-latex-extra texlive-fonts-recommended dvipng cm-super && \ 
     # Clean up
     rm -rf /var/lib/apt/lists/*


# Setup Backend
COPY requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt
COPY . .


# Serve the API
EXPOSE 8000
CMD ["python3", "-u", "main.py", "--serve-api"]
