# Create a flask web application to recommend products to a user
from flask import Flask, request, jsonify
import pickle
import json

app = Flask(__name__)

# create a init function that read all the pickled files and store them as global variables
def init():
    global user_product_interaction_with_category, user_product_interaction_with_product_id, user_similarity_df, product_details_df
    with open('user_product_interaction_with_category.pkl', 'rb') as f:
        user_product_interaction_with_category = pickle.load(f)
    with open('user_product_interaction_with_product_id.pkl', 'rb') as f:
        user_product_interaction_with_product_id = pickle.load(f)
    with open('user_similarity_df.pkl', 'rb') as f:
        user_similarity_df = pickle.load(f)
    with open('product_details_df.pkl', 'rb') as f:
        product_details_df = pickle.load(f)

# create a function to find the most similar users
def most_similar_users(user_id, user_similarity, topn=10):
    user = user_similarity[user_id]
    return user.argsort()[::-1][1:topn+1]

# create function to recommend products to a user
def recommend_products(user_id, user_product_interaction_category, user_product_interaction, user_similarity, topn=10, purchased_category_treshold=2):
    reommended_products = []

    
    # find the products that the user_id has already purchased
    products_purchased_category = user_product_interaction_category.loc[user_id]
    products_purchased_product_id = user_product_interaction.loc[user_id]

    products_purchased_category = products_purchased_category[products_purchased_category > purchased_category_treshold].sort_values(ascending=False)    
    product_ids_from_reccurance_purchased = product_details_df.apply(lambda x: {"product_id": x['product_id'], "category": x['category']} if x['category'] in products_purchased_category.index else None, axis=1)
    product_ids_from_reccurance_purchased = product_ids_from_reccurance_purchased.dropna()
    # obtain one item for each category from product_ids_from_reccurance_purchased where product_id is not in products_purchased_product_id
    selected_categories = {}
    # print(products_purchased_product_id[products_purchased_product_id > 0])
    # print(product_ids_from_reccurance_purchased)
    for row in product_ids_from_reccurance_purchased:
        if row['product_id'] not in products_purchased_product_id[products_purchased_product_id > 0] and selected_categories.get(row['category']) == None:
            reommended_products.append(row['product_id'])
            selected_categories[row['category']] = True

    # find the most similar users to the user_id
    most_similar = most_similar_users(user_id, user_similarity, topn)
    most_similar = most_similar[most_similar > 0]
    similar_users = user_product_interaction_category.loc[most_similar]
    # sum the purchase count of each product by similar users
    recommendations = similar_users.sum().sort_values(ascending=False)
    recommendations = recommendations.drop(products_purchased_category[products_purchased_category > 0].index, errors='ignore')

    if(len(reommended_products) < topn):
        for category in recommendations.index:
            product_id = product_details_df[product_details_df['category'] == category].iloc[0]['product_id']
            if product_id not in products_purchased_product_id[products_purchased_product_id > 0]:
                reommended_products.append(product_id)
                if(len(reommended_products) >= topn):
                    break
 
    return reommended_products

@app.route('/recommend', methods=['GET'])
def recommend():
    global user_product_interaction_with_category, user_product_interaction_with_product_id, user_similarity_df, product_details_df
    user_id = int(request.args.get('user_id'))
    topn = int(request.args.get('topn'))
    purchased_category_treshold = 2
    recommended_products = recommend_products(user_id, user_product_interaction_with_category, user_product_interaction_with_product_id, user_similarity_df, topn, purchased_category_treshold)
    response = [  int(product_id) for product_id in recommended_products]

    return jsonify({"data": {"recommendedProducts": response}})

if __name__ == '__main__':
    init()
    app.run(debug=True, port=5000)