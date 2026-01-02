# 🧪 Lab Mall Bot Backend

A scalable Python/FastAPI microservice designed to power the Lab Mall WhatsApp Chatbot. This system allows users to search extensive chemical catalogs (Fresh Stock & Clearance), viewing real-time pricing with GST calculations, and managing separate carts for retail and quote-based items.

## 🚀 Key Features

* **Smart Chemical Search:** Hybrid search algorithm combining MySQL Full-Text Search (Boolean Mode) and Wildcard matching to find chemicals by Name, CAS Number, or SKU Code.
* **Dual-Cart System:**
    * **Fresh Stock:** Standard e-commerce flow (Add to Cart → Checkout → Payment).
    * **Clearance/Dead Stock:** Inquiry flow (Add to List → Submit Quote Request).
* **Dynamic Pricing Engine:** Automatically displays "List Price" vs. "LabMall Discounted Price" and calculates GST on the fly.
* **User Session Management:** Caches search results and tracks user state to handle WhatsApp conversational flows (e.g., pagination, selection).
* **Cloud Native:** Dockerized application deployed on Google Cloud Run with a Google Cloud SQL (MySQL) backend.

## 🛠️ Tech Stack

* **Language:** Python 3.9+
* **Framework:** FastAPI
* **Database:** MySQL (PyMySQL + Cloud SQL Connector)
* **Deployment:** Docker & Google Cloud Run
* **Tools:** Pandas (for data import), Uvicorn

## 📂 Project Structure

* `main.py`: Core application logic, API endpoints, and routing.
* `crud.py`: Database operations (Search logic, Cart management, Order creation).
* `db.py`: Database connection handler (Auto-detects Local vs. Cloud environment).
* `models.py`: Pydantic models for data validation.
* `Dockerfile`: Configuration for building the production container.

## ⚙️ Local Development Setup

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/lab-mall-bot.git](https://github.com/YOUR_USERNAME/lab-mall-bot.git)
    cd lab-mall-bot
    ```

2.  **Create a virtual environment**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use: venv\Scripts\activate
    ```

3.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up Local Database**
    * Ensure MySQL is running locally.
    * Create a database named `shopify`.
    * Import the schema (or `shopify_backup.sql`).

5.  **Run the Server**
    ```bash
    uvicorn main:app --reload
    ```
    The API will be available at `http://127.0.0.1:8000`.

## ☁️ Deployment (Google Cloud)

This project is optimized for Google Cloud Run.

### 1. Build the Image
*Note: Use `--platform linux/amd64` if building on an Apple Silicon (M1/M2/M3) Mac.*
```bash
docker build --platform linux/amd64 -t gcr.io/lab-mall-bot-2025/lab-mall-service .
