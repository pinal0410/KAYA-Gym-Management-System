# KAYA – Gym & Fitness Management System

## About the Project

KAYA is a Gym and Fitness Management System developed to make gym management easier and more organized. It helps manage members, trainers, memberships, bookings, workout plans, attendance, and payments.

The system is developed using Python, Streamlit, and MySQL.

## Features

- **Admin Management:** Manage members, trainers, membership plans, bookings, and payments.
- **Member Management:** Register members and maintain their personal and fitness information.
- **Membership Management:** Create and manage membership plans and memberships.
- **Trainer Management:** Maintain trainer information.
- **Booking Management:** Manage member bookings with trainers.
- **Workout Plans:** Create and manage workout plans.
- **Attendance Management:** Maintain member attendance records.
- **Payment Management:** Manage membership payment records.
- **Login System:** Separate access for Admin, Trainer, and Member accounts.

## Technologies Used

- Python
- Streamlit
- MySQL
- Pandas

## Project Structure

- **KAYA-Gym-Management-System**
  - app.py
  - auth.py
  - db_connection.py
  - **pages/**
    - 1_Members.py
    - 2_Membership_Plans.py
    - 3_Memberships.py
    - 4_Bookings.py
    - 5_Trainers.py
    - 6_Workout_Plans.py
    - 7_Attendence.py
    - 8_Payments.py
  - **.streamlit/**
    - config.toml
  - .gitignore

## How to Run the Project

1. Install Python and MySQL.
2. Install the required Python packages.
3. Create a MySQL database named `gym_management`.
4. Configure your local database connection settings.
5. Open the project folder in VS Code.
6. Open the terminal in the project folder.
7. Run the following command:

   `python -m streamlit run app.py`

## Future Enhancements

- Generate detailed gym reports.
- Add automated notifications.
- Improve fitness tracking features.
- Add more member activity insights.

## Project Type

Software Engineering – Open Ended Project (OEP)

## Developer

Developed as a college academic project.
