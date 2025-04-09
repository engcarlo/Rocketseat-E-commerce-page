#%% Bibliotecas
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user

#%% Configurações
app = Flask(__name__)
app.config['SECRET_KEY'] = 'minha_chave_123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'

login_manager = LoginManager()
db = SQLAlchemy(app) # Inicializa o banco de dados com a aplicação FLask
login_manager.init_app(app)
login_manager.login_view = 'login' # Rota de login
CORS(app) # permite que outros sistemas acessem 


#%% Modelagem de Dados 
# Usuário User (id, username, password)
class User(db.Model, UserMixin):
    id          = db.Column(db.Integer, primary_key = True)
    username    = db.Column(db.String(80), nullable = False, unique = True)
    password    = db.Column(db.String(80), nullable = True)
    cart        = db.relationship('CartItem', backref = 'user', lazy = True)

# Produto (id, name, price, description)
class Product(db.Model):
    id          = db.Column(db.Integer, primary_key = True)
    name        = db.Column(db.String(120), nullable = False)
    price       = db.Column(db.Float, nullable = False)
    description = db.Column(db.Text, nullable = True)

# Carrinho
class CartItem(db.Model):
    id          = db.Column(db.Integer, primary_key = True)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    product_id  = db.Column(db.Integer, db.ForeignKey('product.id'), nullable = False)

#%% Aplicação WEB
# Autenticação
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Rota de Login
@app.route('/login', methods = ["POST"])
def login():
    data = request.json
    user = User.query.filter_by(username = data.get("username")).first()
    
    if user and data.get("password") == user.password:
        login_user(user)
        return jsonify({'message': 'Usuário Logado com Sucesso!'}), 200

    return jsonify({'message': 'Usuário Não Autorizado'}), 401

# Rota de Logout
@app.route('/logout', methods = ["POST"])
@login_required
def logout():
    logout_user()
    return jsonify(**{'result': 200,
                      'data': {'message': 'Logout com Sucesso!'}})

# Rota de Informação do Usuário
@app.route('/user_info', methods=['POST'])
def user_info():
    if current_user.is_authenticated:
        resp = {"result": 200,
                "data": current_user.to_json()}
    else:                                                                                                                    
        resp = {"result": 401,
                "data": {"message": "Usuário não Logado!"}}
    return jsonify(**resp)

#%% Funções de Manipulação
# Rota para Adicionar Produto
@app.route('/api/products/add', methods = ["POST"])
@login_required
def add_product():
    # Recuperar o produto da requisição (request)
    data = request.json
    # Verificar se as informações necessárias estão presentes
    if 'name' in data and 'price' in data:
        # Se sim, criar um novo produto e adicionar ao banco de dados
        product = Product(
                        name          = data['name'],
                        price         = data['price'],
                        description   = data.get('description', ''))
        db.session.add(product)
        db.session.commit()
        return jsonify({'message': 'Produto Cadastrado com Sucesso!'}), 200
    return jsonify({'message': 'Invalid Product Data'}), 400 # quando o dado é inexperado/inválido

# Rota para Deletar Produto
@app.route('/api/products/delete/<int:product_id>', methods = ["DELETE"])
@login_required
def delete_product(product_id):
    # Recuperar o produto da base de dados
    product = Product.query.get(product_id)
    # Verificar se o produto existe
    if product:
        # Se existe, apagar da base de dados
        db.session.delete(product)
        db.session.commit()
        # Retornar mensagem de sucesso
        return jsonify({'message': 'Produto Deletado com Sucesso!'}), 200
    # Se não existe, retornar 404 not found
    return jsonify({'message': 'Produto Não Encontrado'}), 404 #  quando não existe o dado inserido

# Rota para Recuperar Informações de um Produto
@app.route('/api/products/<int:product_id>', methods = ["GET"])
def get_product_details(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify({
            'id':           product.id,
            'name':         product.name,
            'price':        product.price,
            'description':  product.description
        })
    return jsonify({"message": "Produto não Encotrado!"}), 404

# Rota para Atualizar Produto
@app.route('/api/products/update/<int:product_id>', methods = ["PUT"])
@login_required
def update_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"message": "Produto não Encotrado!"}), 404

    data = request.json
    if 'name' in data:
        product.name = data['name']

    if 'price' in data:
        product.price = data['price']
    
    if 'description' in data:
        product.description = data['description']

    db.session.commit()
    return jsonify({"message": "Produto Atualizado com Sucesso!"}), 200

# Rota para Retornar a Lista de Produtos
@app.route('/api/products', methods = ["GET"])
def get_products():
    products = Product.query.all()
    product_list = []
    for product in products:
        product_data = {
            'id':           product.id,
            'name':         product.name,
            'price':        product.price,
            'description':  product.description
        }
        product_list.append(product_data)
    return jsonify(product_list), 200


#%% Marketplace
# Adição de Item
@app.route('/api/cart/add/<int:product_id>', methods = ["POST"])
@login_required
def add_to_cart(product_id):
    # Usuário
    user = User.query.get(int(current_user.id))
    #Produto
    product = Product.query.get(product_id)
    # Verifica se os retornos são válidos
    if product:
        cart_item = CartItem(user_id = user.id, product_id = product.id)
        db.session.add(cart_item)
        db.session.commit()
        # Retornar mensagem de sucesso
        return jsonify({'message': 'Item adicionado ao seu carrinho'}), 200
    else: 
        return jsonify({'message': 'Item Não Exite'}), 404
    # Se não existe, retornar 404 not found
    return 

# Remoção de Item
@app.route('/api/cart/remove/<int:product_id>', methods = ["DELETE"])
@login_required
def remove_from_cart(product_id):
    # Produto, Usuário = Item no Carrinho
    cart_item = CartItem.query.filter_by(user_id = current_user.id, product_id = product_id).first()
    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()
        return jsonify({'message': 'Item removido do carrinho com sucesso'}), 200
    return jsonify({'message': 'Falha ao Remover Item do carrinho'}), 400

@app.route('/api/cart', methods = ['GET'])
@login_required
def view_cart():
    # Usuário
    user = User.query.get(int(current_user.id))
    cart_items = user.cart
    cart_content = []
    for cart_item in cart_items:
        product = Product.query.get(cart_item.product_id)
        cart_content.append({
            "id": cart_item.id,
            "user_id": cart_item.user_id,
            "product_id": cart_item.product_id,
            "product_name": product.name,
            "product_price": product.price
        })

    return jsonify(cart_content)

# Checkout
@app.route('/api/cart/checkout', methods = ["POST"])
@login_required
def checkout():
    user = User.query.get(int(current_user.id))
    cart_items = user.cart
    for cart_item in cart_items:
        db.session.delete(cart_item)
    db.session.commit()
    return jsonify({'message': 'Checkout Concluído com Sucesso. Basqueta foi esvaziada!.'})

# Definir uma rota raiz (página inicial) e a função que será executada ao requisitar
@app.route('/')
def hello_world():
    return "Hello, World!"

if __name__ == '__main__':
    app.run(debug=True) # Debug para facilitar o desenvolvimento e identificar causas de problemas
