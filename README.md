# hospital-management-system
This is a basic project of Hospital Management System (HMS) a web application that allows Admins, Doctors, and Patients to interact with the system based on their roles.

## How to Run the Application

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Installation & Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd hospital-management-system
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
     ```bash
     venv\Scripts\activate


4. **Install required dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the application**
   - Open your web browser and navigate to: `http://127.0.0.1:5000`
   - The database will be automatically created on first run

### Default Admin Credentials
- **Username:** `admin`
- **Password:** `admin123`

### Features
- **Admin Panel:** Manage doctors, patients, appointments, and view treatment histories
- **Doctor Panel:** View appointments, manage availability, add treatment records
- **Patient Panel:** Book appointments, view treatment history, edit profile
- **Working Hours:** 10 AM - 5 PM (Weekdays only, weekends off)
- **Blacklist System:** Admin can blacklist doctors and patients

