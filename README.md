# Readme.md

![image](https://github.com/user-attachments/assets/4b3d3244-ef37-4f2f-abc0-65cc674a48d0)

## Short Description of our Project
The Smart Shelf project is an IoT-based inventory management system designed to monitor and manage stock levels in real-time. Utilizing sensors and cloud services, the system alerts users when stock levels are low, ensuring timely restocking and efficient inventory management.

## Motivation
The motivation behind the Smart Shelf project is to streamline inventory management processes, reduce manual labor, and prevent stockouts. By leveraging IoT technology, businesses can maintain optimal stock levels, enhance operational efficiency, and improve customer satisfaction.

## MVP/North Star
The MVP of the Smart Shelf project is a functional system that includes sensor integration, data processing, and real-time notifications for low stock levels. The North Star goal is to develop a comprehensive inventory management solution with advanced analytics and automated restocking capabilities.

## Architecture (Logical and Technical)

### Logical Architecture
1. **Sensors**: Load cells to measure the weight of items on the shelf.
2. **IoT Hub**: Collects data from sensors and forwards it to the cloud.
3. **Stream Analytics**: Processes incoming data streams in real-time.
4. **Cosmos DB**: Stores processed data for historical analysis and reporting.
5. **Logic Apps**: Triggers notifications based on predefined conditions.
6. **Notification Service**: Sends alerts via email or other messaging services when stock levels are low.

### Technical Architecture. 

1. **Hardware Components**:
   - Load cells
   - Microcontroller (Raspberry Pi)
   - Amplifier (HX711)
2. **Software Components**:
   - IoT Hub for device communication
   - Stream Analytics for data processing
   - Cosmos DB for data storage
   - Logic Apps for workflow automation
   - Notification service

   ![image](https://github.com/user-attachments/assets/6860032f-a6f2-4fd8-9e8c-1da8eb512dfb)




### "How to Set Up!"

#### Hardware Setup
1. **Connect Load Cells**: Connect load cells to each other to form a full bridge.
2. **Connect Amplifier**: Connect the HX711 amplifier to the load cells.
3. **Connect Microcontroller**: Connect the HX711 with the microcontroller.
4. **Microcontroller Configuration**: Program the microcontroller to read data from load cells.

#### Software Setup
1. **Create Azure IoT Hub**: Set up an IoT Hub in Azure to receive data from the microcontroller.
2. **Stream Analytics Job**:
    - Create a Stream Analytics job to process data from the IoT Hub.
    - Define input (IoT Hub) and output (Cosmos DB) for the job.
    - Write a query to process incoming data and store it in Cosmos DB.
3. **Cosmos DB Setup**:
    - Create a Cosmos DB account and a database to store processed data.
    - Define the necessary containers for data storage.
4. **Logic Apps Configuration**:
    - Create a Logic App to monitor Cosmos DB for low stock levels.
    - Define conditions for triggering notifications.
    - Set up actions to send notifications via email or other services.
5. **Notification Service**:
    - Integrate a notification service (e.g., SendGrid) with Logic Apps to send email alerts.
    - Configure email templates and recipients.

1. **Raspberry Pi Setup**
    - Connect weight sensors to Raspberry Pi.
    - Install necessary libraries:
      ```bash
      sudo apt-get update
      sudo apt-get install python3-pip
      pip3 install RPi.GPIO hx711 azure-iot-device
      ```
    - Clone the project repository:
      ```bash
      git clone <repository-url>
      cd project-directory
      python3 src/calibration.py  # Calibrate the sensors
      python3 src/Main.py  # Start data collection
      ```
#### Code Setup

Creating and activating a virtual environment in Python is straightforward on both Windows and Mac. Below are the steps for each platform:

### Windows

1. **Install Python:** Ensure Python is installed. You can download it from the [official Python website](https://www.python.org/).
2. **Open Command Prompt:**
   - Press `Win + R`, type `cmd`, and press Enter.
3. **Navigate to your project directory:**

   ```sh
   cd path\to\your\project
   ```
4. **Create a virtual environment:**

   ```sh
   python -m venv env
   ```

   Here, `env` is the name of the virtual environment directory. You can name it anything you like.
5. **Activate the virtual environment:**

   ```sh
   .\env\Scripts\activate
   ```

   You should see `(env)` prepended to your command prompt, indicating the virtual environment is active.
6. **Deactivate the virtual environment:**

   ```sh
   deactivate
   ```

### Mac

1. **Install Python:** Ensure Python is installed. You can download it from the [official Python website](https://www.python.org/) or use a package manager like Homebrew (`brew install python`).
2. **Open Terminal:**
   - Press `Cmd + Space`, type `Terminal`, and press Enter.
3. **Navigate to your project directory:**

   ```sh
   cd /path/to/your/project
   ```
4. **Create a virtual environment:**

   ```sh
   python3 -m venv env
   ```

   Here, `env` is the name of the virtual environment directory. You can name it anything you like.
5. **Activate the virtual environment:**

   ```sh
   source env/bin/activate
   ```

   You should see `(env)` prepended to your command prompt, indicating the virtual environment is active.
6. **Deactivate the virtual environment:**

   ```sh
   deactivate
   ```

### Additional Tips

- **Installing from requirements file:** To install packages from a `requirements.txt` file:

  ```sh
  pip install -r src/requirements.txt
  ```

### Costs
1. **Hardware Costs**:
    - Load cells + Amplifier: $13.99
    - Microcontroller: $35
    - Board: $2.54
2. **Azure Services**:
    
    ![cost1.png](load-cell/images/cost1.png)

    ![cost2.png](load-cell/images/cost2.png)


