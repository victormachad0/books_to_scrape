import re
import datetime
import requests
import pandas as pd

from bs4 import BeautifulSoup


def data_collect(url, headers):
    aux_details = []

    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.text, 'html.parser')

    total_products = soup.find_all('form', class_="form-horizontal")[0].get_text().split('\n')  # 1000
    total_products = list(filter(None, total_products))[0]
    total_products = total_products[0:4]

    # Total de paginas no site
    pages_number = round(int(total_products) / 20)  # 50

    df_aux = pd.DataFrame(columns=['title', 'price', 'star_rate'])

    for i in range(1, pages_number + 1):


        # pagina a pagina até a ultima do catalogo
        url = 'https://books.toscrape.com/catalogue/page-' + str(i) + '.html'

        # api request
        page = requests.get(url, headers=headers)
        soup = BeautifulSoup(page.text, 'html.parser')

        all_products = soup.find('ol', class_='row')  # vitrine
        product_list = all_products.find_all('a', href=True)  # link de cada pagina

        # Pegando o nome dos titulos de cada livro
        list_title = soup.find_all('a', href=True)

        title = [i.get('title') for i in list_title]

        # Fazendo a limpeza dos "None's" que vieram junto
        title = list(filter(None, title))

        # Pegando o preço de cada livro
        list_price = soup.find_all('p', class_='price_color')

        prices = [i.get_text() for i in list_price]

        # Avaliações dos clientes
        evaluation_list = soup.find_all('p', class_='star-rating')

        evaluation = [i.get('class')[1] for i in evaluation_list]

        # Criando um dataframe
        data = pd.DataFrame([title, prices, evaluation]).T
        data.columns = ['title', 'price', 'star_rate']

        data['scrapy_datetime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        df_aux = pd.concat([df_aux, data], axis=0)


        for i in range(1, 40, 2):
            aux_details.append(product_list[i]['href'])

    return df_aux, aux_details

def data_details(df_aux, aux_details, headers):
    aux_title = []
    aux_availability = []
    aux_reviews = []
    aux_category = []

    for i in range(len(aux_details)):


        url = 'https://books.toscrape.com/catalogue/' + aux_details[i]
        page = requests.get(url, headers=headers)

        soup = BeautifulSoup(page.text, 'html.parser')

        title = soup.find_all('h1')[0].get_text()
        aux_title.append(title)

        # Estoque de produtos
        product_availability = soup.find_all('p', class_='instock availability')[0].get_text().split('\n')
        product_availability = product_availability[3]

        aux_availability.append(product_availability)

        # Avaliação do produto
        product_review = soup.find_all('td')[6].get_text()

        aux_reviews.append(product_review)

        # Categoria do livro
        book_category = soup.find_all('a', href=True)[3].get_text()

        aux_category.append(book_category)

        df_details = pd.DataFrame([aux_title, aux_category, aux_availability, aux_reviews]).T
        df_details.columns = ['title', 'book_category', 'stock', 'book_review']

        data_final = pd.merge(df_details, df_aux, on='title', how='left')
        data_final = data_final[['title', 'book_category', 'price', 'star_rate', 'stock']].copy()

    return data_final

def data_transform(data):

    # Colocando os nomes dos meus titulos em minusculo
    data['title'] = data['title'].apply(lambda x: x.lower() if pd.notnull(x) else x)

    # Colocando as categorias dos livros em minusculo
    data['book_category'] = data['book_category'].apply(lambda x: x.lower() if pd.notnull(x) else x)

    # Retirando os caracteres 'Â£' do meu preço
    data['price'] = data['price'].apply(lambda x: x.replace('Â£', '')).astype(float)

    # star rate para numerico
    data['star_rate'] = data['star_rate'].apply(lambda x: 1 if x == 'One' else
                                                          2 if x == 'Two' else
                                                          3 if x == 'Three' else
                                                          4 if x == 'Four' else 5).astype('int64')

    # Pegando somente o numero de avaliações
    data['stock'] = data['stock'].apply(lambda x: re.search('\d?\d', x).group(0) if pd.notnull(x) else x).astype('int64')

    # Removendo duplicidades do meu dataframe
    data = data.drop_duplicates(keep='last')

    return data


if __name__ == '__main__':
    url = 'https://books.toscrape.com/'
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

    df_aux, aux_details = data_collect(url, headers)
    data_raw = data_details(df_aux, aux_details, headers)
    data_final = data_transform(data_raw)