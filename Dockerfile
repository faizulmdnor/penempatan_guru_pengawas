FROM python:3.9

# Set the working directory
WORKDIR /app

# Copy all project files into the container
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Initialize the database
RUN python -c 'from pengawas_exam import init_db; init_db()'

# Expose port and run the app
EXPOSE 6060
CMD ["python", "pengawas_exam.py"]
