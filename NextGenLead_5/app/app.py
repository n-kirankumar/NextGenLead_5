import psycopg2
from flask import Flask, request, jsonify
from flask_restful import Api
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, TIMESTAMP, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

app = Flask(__name__)
api = Api(app)

# Database setup
Base = declarative_base()
database_url = "postgresql://postgres:1234@localhost:5432/postgres"
engine = create_engine(database_url, echo=True, poolclass=NullPool)
Session = sessionmaker(bind=engine)
session = Session()

# Define the customer_interactions model
class CustomerInteraction(Base):
    __tablename__ = 'customer_interactions'

    interaction_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_name = Column(String(100), nullable=False)
    phone_number = Column(String(20), nullable=False)
    request_type = Column(String(50), nullable=False)
    preferred_time = Column(DateTime)
    additional_info = Column(Text)
    dealer_name = Column(String(100))
    dealer_phone_number = Column(String(20))
    interaction_summary = Column(Text)
    next_steps = Column(String(255))
    customer_status = Column(String(50), nullable=False, default='Pending')
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

# Create the table if it doesn't exist
Base.metadata.create_all(engine)

# POST: Submit Callback Request (Step 1)
@app.route('/api/callback-request', methods=['POST'])
def create_callback_request():
    data = request.json
    new_request = CustomerInteraction(
        customer_name=data.get('customer_name'),
        phone_number=data.get('phone_number'),
        request_type=data.get('request_type'),
        preferred_time=data.get('preferred_time'),
        customer_status='Pending'
    )
    session.add(new_request)
    session.commit()
    return jsonify({
        "status": "success",
        "message": "Callback request created",
        "request_id": new_request.interaction_id
    })

# PUT: Update Callback Request (Step 2)
@app.route('/api/callback-request/<int:request_id>', methods=['PUT'])
def update_callback_request(request_id):
    data = request.json
    # Find the existing callback request by the request_id
    callback_request = session.query(CustomerInteraction).filter_by(interaction_id=request_id).first()

    if not callback_request:
        return jsonify({
            "status": "error",
            "message": f"Request with id {request_id} not found"
        }), 404

    # Update fields based on the provided data
    callback_request.customer_name = data.get('customer_name', callback_request.customer_name)
    callback_request.additional_info = data.get('additional_info', callback_request.additional_info)

    session.commit()

    return jsonify({
        "status": "success",
        "message": "Request updated successfully"
    })

# GET: Retrieve Customer Info for Dealers (Step 3)
@app.route('/api/customer-info/<int:interaction_id>', methods=['GET'])
def get_customer_info(interaction_id):
    # Query to fetch customer information for a specific interaction_id
    customer = session.query(CustomerInteraction).filter_by(interaction_id=interaction_id).first()

    if not customer:
        return jsonify({
            "status": "error",
            "message": f"No customer information found for interaction ID {interaction_id}"
        }), 404

    # Serialize customer data
    customer_data = {
        "customer_name": customer.customer_name,
        "phone_number": customer.phone_number,
        "request_type": customer.request_type,
        "additional_info": customer.additional_info,
        "preferred_time": customer.preferred_time,
        "dealer_name": customer.dealer_name
    }

    return jsonify(customer_data)

# PUT: Record Dealer-Customer Interaction (Step 6)
@app.route('/api/customer-interaction/<int:interaction_id>', methods=['PUT'])
def update_customer_interaction(interaction_id):
    data = request.json
    interaction = session.query(CustomerInteraction).filter_by(interaction_id=interaction_id).first()

    if not interaction:
        return jsonify({
            "status": "error",
            "message": f"Interaction with id {interaction_id} not found"
        }), 404

    # Update interaction details
    interaction.interaction_summary = data.get('interaction_summary', interaction.interaction_summary)
    interaction.next_steps = data.get('next_steps', interaction.next_steps)
    interaction.customer_status = data.get('customer_status', interaction.customer_status)

    session.commit()

    return jsonify({
        "status": "success",
        "message": "Interaction details updated successfully"
    })


@app.route('/api/sales-interaction/<int:interaction_id>', methods=['PUT'])
def record_sales_interaction(interaction_id):
    data = request.json
    interaction = session.query(CustomerInteraction).filter_by(interaction_id=interaction_id).first()

    if not interaction:
        return jsonify({
            "status": "error",
            "message": f"Interaction with id {interaction_id} not found"
        }), 404

    # Update salesperson interaction details
    interaction.interaction_summary = data.get('interaction_summary', interaction.interaction_summary)
    interaction.next_steps = data.get('next_steps', interaction.next_steps)
    interaction.customer_status = data.get('customer_status', interaction.customer_status)

    session.commit()

    return jsonify({
        "status": "success",
        "message": "Salesperson interaction details recorded successfully"
    })


@app.route('/api/reports/customer-status', methods=['GET'])
def get_customer_status_report():
    interactions = session.query(CustomerInteraction).all()

    # Serialize interaction data for reporting
    report_data = [{
        "customer_name": interaction.customer_name,
        "status": interaction.customer_status,
        "interaction_summary": interaction.interaction_summary,
        "dealer_name": interaction.dealer_name
    } for interaction in interactions]

    return jsonify(report_data)

if __name__ == '__main__':
    app.run(debug=True)
