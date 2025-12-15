"""Flask API for the banking chatbot service."""
from flask import Flask, request, jsonify
from chatbot_service import BankingChatbot
import config

app = Flask(__name__)
chatbot = BankingChatbot()


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "banking-chatbot"
    }), 200


@app.route('/chat', methods=['POST'])
def chat():
    """
    Main chat endpoint for natural language queries.
    
    Request body:
    {
        "customer_id": "CUST001",
        "query": "What's my current EMI and can I prepay this month?"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'customer_id' not in data or 'query' not in data:
            return jsonify({
                "error": "Missing required fields: customer_id and query"
            }), 400
        
        customer_id = data['customer_id']
        query = data['query']
        
        # Process the query
        result = chatbot.process_query(customer_id, query)
        
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


@app.route('/prepayment/calculate', methods=['POST'])
def calculate_prepayment():
    """
    Calculate prepayment amount with charges.
    
    Request body:
    {
        "customer_id": "CUST001",
        "loan_id": "LOAN001",
        "prepayment_amount": 100000
    }
    """
    try:
        data = request.get_json()
        
        required_fields = ['customer_id', 'loan_id', 'prepayment_amount']
        if not data or not all(field in data for field in required_fields):
            return jsonify({
                "error": f"Missing required fields: {', '.join(required_fields)}"
            }), 400
        
        customer_id = data['customer_id']
        loan_id = data['loan_id']
        prepayment_amount = float(data['prepayment_amount'])
        
        # Calculate prepayment
        result = chatbot.calculate_prepayment(customer_id, loan_id, prepayment_amount)
        
        return jsonify(result), 200
    
    except ValueError:
        return jsonify({
            "error": "Invalid prepayment_amount: must be a number"
        }), 400
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


@app.route('/customer/<customer_id>/summary', methods=['GET'])
def get_customer_summary(customer_id):
    """
    Get customer account and loan summary.
    
    Path parameter:
        customer_id: Customer identifier
    """
    try:
        summary = chatbot.get_customer_summary(customer_id)
        
        if not summary:
            return jsonify({
                "error": "Customer not found"
            }), 404
        
        return jsonify(summary), 200
    
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


@app.route('/search/faqs', methods=['POST'])
def search_faqs():
    """
    Search FAQs using semantic search.
    
    Request body:
    {
        "query": "What is EMI?",
        "n_results": 3
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                "error": "Missing required field: query"
            }), 400
        
        query = data['query']
        n_results = data.get('n_results', 3)
        
        results = chatbot.vector_db.search_faqs(query, n_results)
        
        return jsonify({
            "query": query,
            "results": results
        }), 200
    
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


@app.route('/search/policies', methods=['POST'])
def search_policies():
    """
    Search policy documents using semantic search.
    
    Request body:
    {
        "query": "prepayment charges",
        "n_results": 3
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                "error": "Missing required field: query"
            }), 400
        
        query = data['query']
        n_results = data.get('n_results', 3)
        
        results = chatbot.vector_db.search_policies(query, n_results)
        
        return jsonify({
            "query": query,
            "results": results
        }), 200
    
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


if __name__ == '__main__':
    print("Starting Banking Chatbot Service...")
    print(f"Server running on http://{config.FLASK_HOST}:{config.FLASK_PORT}")
    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG
    )
