import numpy as np
import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
from urllib.parse import urljoin, urlparse
import os
from openai import AzureOpenAI, OpenAI
import tiktoken

############################### Scrape CTM website ################################

# Initialize base URL and visited links set
base_url = "https://au.travelctm.com/"  # The starting point of our crawl
visited_links = set()  # To keep track of visited URLs and avoid duplicates
page_counter = 0  # Counter to keep track of the number of pages scraped


def scrape_page(url):
    """
    Scrapes the content of a given page.
    :param url: The URL of the page to scrape
    :return: The text content of the page and the BeautifulSoup object
    """
    response = requests.get(url)
    if response.status_code == 200:  # Check if the request was successful
        soup = BeautifulSoup(response.content, "html.parser")

        # Remove header and footer content
        for element in soup.find_all(["header", "footer"]):
            element.decompose()

        # Extract text from all paragraph and header tags, excluding header and footer
        text_content = " ".join(
            [
                p.get_text(strip=True)
                for p in soup.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6"])
            ]
        )

        # Remove the unwanted initial string
        unwanted_string = (
            "Local solutions, delivered globally CTM provides local service solutions to "
            "customers around the world. Please select your local region, and start experiencing "
            "the CTM difference!   Don’t show this again"
        )
        text_content = text_content.replace(unwanted_string, "").strip()

        return text_content, soup
    return None, None


def is_internal_link(link):
    """
    Determines if a link is internal (i.e., part of the same domain).
    :param link: The URL to check
    :return: True if the link is internal, False otherwise
    """
    parsed_link = urlparse(link)
    return (
        parsed_link.netloc == "" or parsed_link.netloc == urlparse(base_url).netloc
    ) and not parsed_link.scheme == "mailto"


def get_internal_links(soup, base_url):
    """
    Extracts all internal links from a BeautifulSoup object.
    :param soup: The BeautifulSoup object containing the page content
    :param base_url: The base URL to resolve relative links
    :return: A set of full URLs that are internal links
    """
    links = set()
    for item in soup.find_all("a", href=True):
        href = item["href"]
        if is_internal_link(href):
            # Convert relative URL to absolute URL
            full_url = urljoin(base_url, href)
            links.add(full_url)
    return links


def scrape_website(base_url):
    """
    Manages the scraping of the entire website by following internal links.
    :param base_url: The starting URL of the website
    :return: A list of dictionaries containing URLs and their respective text content
    """
    to_visit = [base_url]  # List of URLs to visit, starting with the base URL
    data = []  # List to store the scraped data
    global page_counter  # Declare page_counter as a global variable

    while to_visit:
        current_url = to_visit.pop(0)  # Get the next URL to visit
        if current_url not in visited_links:
            print(f"Scraping: {current_url}")
            visited_links.add(current_url)  # Mark the URL as visited
            text_content, soup = scrape_page(current_url)  # Scrape the page
            if text_content:
                # Add the URL and its text content to the data list
                data.append({"URL": current_url, "Content": text_content})
                page_counter += 1  # Increment the page counter
                print(f"Page counter: {page_counter}")
                # Get all internal links from the page and add them to the to_visit list
                internal_links = get_internal_links(soup, base_url)
                to_visit.extend(internal_links)
            # Be polite to the server by adding a delay between requests
            time.sleep(1)

    return data


# Scrape the website and save data to CSV
# scraped_data = scrape_website(base_url)
# df = pd.DataFrame(scraped_data)  # Convert the data to a DataFrame
# df.to_csv("website_data.csv", index=False)  # Save the DataFrame to a CSV file
# print(f"Data saved to website_data.csv. Total pages scraped: {page_counter}")


############################### Generate Embeddings ################################


# Initialize OpenAI API key
# client = AzureOpenAI(
#     api_key=os.getenv("AZURE_OPENAI_API_KEY"),
#     api_version="2024-02-15-preview",
#     azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
# )

client = OpenAI()

# response = client.embeddings.create(
#     input="Your text string goes here",
#     model="text-embedding-3-small"
# )

# print(response.data[0].embedding)


def generate_embeddings(
    input_csv="website_data.csv",
    output_csv="website_with_embeddings.csv",
    output_pickle="website_with_embeddings.pkl",
):
    # Initialize OpenAI API key
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Load scraped data
    df = pd.read_csv(input_csv)

    def get_embedding(
        text, model="text-embedding-3-small", retry_count=3, wait_time=60
    ):
        """
        Get the embedding for a given text using OpenAI's embedding model.
        :param text: The text to get the embedding for
        :param model: The model to use for generating the embedding
        :param retry_count: The number of times to retry in case of rate limiting
        :param wait_time: The time to wait between retries (in seconds)
        :return: The embedding vector
        """
        text = text.replace("\n", " ")
        tokenizer = tiktoken.get_encoding("cl100k_base")
        tokens = tokenizer.encode(text)

        # Truncate text if it exceeds the token limit
        max_tokens = 8192
        if len(tokens) > max_tokens:
            tokens = tokens[:max_tokens]
            text = tokenizer.decode(tokens)

        for attempt in range(retry_count):
            try:
                response = client.embeddings.create(input=[text], model=model)
                return response.data[0].embedding
            except Exception as e:
                print(f"Error: {e}")
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
        return None

    # Track progress and limit requests per minute
    total_rows = len(df)
    embeddings = []
    requests_per_minute = 60
    request_interval = 60 / requests_per_minute

    for i, row in df.iterrows():
        print(f"Processing row {i+1} of {total_rows}")
        embedding = get_embedding(row["Content"])
        embeddings.append(embedding)
        if (i + 1) % requests_per_minute == 0:
            print("Reached rate limit, waiting for the next minute...")
            time.sleep(60)  # Wait for the next minute to avoid rate limiting
        else:
            time.sleep(
                request_interval
            )  # Wait between requests to avoid hitting the rate limit

    # Add embeddings to DataFrame
    df["embeddings"] = embeddings

    # Save the DataFrame with embeddings to CSV and pickle
    df.to_csv(output_csv, index=False)
    df.to_pickle(output_pickle)
    print(f"Embeddings saved to {output_csv} and {output_pickle}")


# Call the generate_embeddings function
# generate_embeddings()

############################### Load Embeddings and Compute Similarity ################################


# Load DataFrame with embeddings
df = pd.read_pickle("website_with_embeddings.pkl")


def get_embedding(text, model="text-embedding-3-small"):
    """
    Get the embedding for a given text using OpenAI's embedding model.
    :param text: The text to get the embedding for
    :return: The embedding vector
    """
    text = text.replace("\n", " ")
    response = client.embeddings.create(input=[text], model=model)
    return response.data[0].embedding


def compute_similarity(embedding1, embedding2):
    """
    Compute the cosine similarity between two embeddings.
    :param embedding1: First embedding vector
    :param embedding2: Second embedding vector
    :return: Cosine similarity score
    """
    return np.dot(embedding1, embedding2) / (
        np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
    )


def query(question, top_n=4):
    """
    Query the embeddings to find the most similar text content.
    :param question: The question to query
    :param top_n: Number of top similar results to return
    :return: The context generated from the most similar text content
    """
    question_embedding = get_embedding(question)
    df["similarity"] = df["embeddings"].apply(
        lambda x: compute_similarity(question_embedding, x)
    )
    top_results = df.nlargest(top_n, "similarity")
    context = "\n\n".join(top_results["Content"])

    return context


def generate_response(question):
    context = query(question)
    print(f"context: {context}")

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are a AI travel agent, works for CTM. You need to answer the user's question based on the given context, which comes from the CTM website.",
            },
            {
                "role": "user",
                "content": question,
            },
            {
                "role": "assistant",
                "content": f"Please try to answer the user's question based on the context: {context}.",
            },
        ],
    )
    return completion.choices[0].message.content


# Example usage
question = "how to make a booking?"
answer = generate_response(question)
print()
print("Answer to the query:")
print(answer)
