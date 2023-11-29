from SPARQLWrapper import SPARQLWrapper, JSON

LMDB_PREFIX = "<https://triplydb.com/Triply/linkedmdb/vocab/>"
SPARQL_ENDPOINT = "https://api.triplydb.com/datasets/Triply/linkedmdb/services/linkedmdb/sparql"
PROPERTY_NAMES = ["actor", "director", "genre", "cinematographer", "producer", "editor", "writer"]

## Function to receive a list of movies with a given title
def get_movie_id(movie_title):
    query_str = f"""
    PREFIX lmdb: {LMDB_PREFIX}

    SELECT distinct ?movie ?title ?year (GROUP_CONCAT(DISTINCT ?directorName; SEPARATOR=", ") AS ?directors)
    WHERE {{
      ?director a lmdb:Director .
      ?director lmdb:director_name ?directorName .
      ?movie a lmdb:Film .
      ?movie <http://purl.org/dc/terms/title> ?title .
      FILTER(CONTAINS(?title, "{movie_title}"))
      ?movie lmdb:director ?director .
      ?movie <http://purl.org/dc/terms/date> ?date .
      BIND(SUBSTR(?date, 1, 4) AS ?year) .
      FILTER NOT EXISTS {{
        ?otherMovie a lmdb:Film .
        ?otherMovie <http://purl.org/dc/terms/title> ?title .
        ?otherMovie <http://purl.org/dc/terms/date> ?otherDate .
        BIND(SUBSTR(?otherDate, 1, 4) AS ?otherYear) .
        FILTER (?otherYear = ?year && ?otherMovie < ?movie)
        }}
    }}
    """
    
    sparql = SPARQLWrapper(SPARQL_ENDPOINT)
    sparql.setQuery(query_str)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    
    movie_ids = []
    for result in results["results"]["bindings"]:
        movie_id = result["movie"]["value"].split('/')[-1]
        movie_found_title = result["title"]["value"]
        movie_director = result["directors"]["value"]
        movie_year = result["year"]["value"]
        movie_ids.append({"movie_id": movie_id, "movie_title": movie_found_title, "movie_director": movie_director, "movie_year": movie_year})

    return movie_ids

## Function to print list of found movies
def print_movies(movie_list):
    print("Movies found based on title:")
    for i in range(len(movie_list)):
        print(f"{i+1} - {movie_list[i]['movie_title']} ({movie_list[i]['movie_year']}, {movie_list[i]['movie_director']})")

## Function to get attributes for source movie
def get_movie_properties(movie):

    select_line = (" ").join(["?"+prop for prop in PROPERTY_NAMES])
    where_clause_lines = [f"Optional{{{movie} lmdb:{prop} ?{prop} . }}" for prop in PROPERTY_NAMES]
    where_clause = ("\n").join(where_clause_lines)

    query_str = f"""
    PREFIX lmdb: {LMDB_PREFIX}

    SELECT {select_line}
    WHERE {{
        {where_clause}
    }}
    """

    sparql = SPARQLWrapper(SPARQL_ENDPOINT)
    sparql.setQuery(query_str)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    properties = {prop: set() for prop in PROPERTY_NAMES}

    for result in results["results"]["bindings"]:
        for prop in PROPERTY_NAMES:
            if prop in result:
                properties[prop].add(result[prop]["value"])

    return properties

## Function to get recommend movies based on attributes
def get_movie_recommendations(properties, movie):    
    property_lines = []
    for prop, values in properties.items():
        for i, value in enumerate(values):
            property_lines.append(f"""
          {{
            ?movie lmdb:{prop} <{value}> .
            BIND("{prop}{i}" as ?matchedProperty)
          }}""")
    property_lines_combined = ("\nUNION\n").join(property_lines)

    query_str = f"""
    PREFIX lmdb: {LMDB_PREFIX}

    SELECT ?movie ?title ?year (GROUP_CONCAT(DISTINCT ?directorName; SEPARATOR=", ") AS ?directors) (COUNT(DISTINCT ?matchedProperty) as ?score)
    WHERE {{
      ?movie a lmdb:Film .
      ?movie <http://purl.org/dc/terms/title> ?title .
      ?base_movie <http://purl.org/dc/terms/title> ?base_title
      {property_lines_combined}
      ?movie lmdb:director ?director .
      ?director lmdb:director_name ?directorName .
      ?movie <http://purl.org/dc/terms/date> ?date .
      BIND(SUBSTR(?date, 1, 4) AS ?year) .
      FILTER(?base_movie = {movie} && ?title != ?base_title)
    }}
    GROUP BY ?movie ?title ?year ?directors
    ORDER BY DESC(?score)
    LIMIT 12
    """

    sparql = SPARQLWrapper(SPARQL_ENDPOINT)
    sparql.setQuery(query_str)
    sparql.setMethod('POST')
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    recommendations = []
    for result in results["results"]["bindings"]:
        movie_id = result["movie"]["value"].split('/')[-1]
        movie_title = result["title"]["value"]
        movie_director = result["directors"]["value"]
        movie_year = result["year"]["value"]
        score = result["score"]["value"]
        recommendations.append({"movie_id": movie_id, "movie_title": movie_title, "movie_director": movie_director, "movie_year": movie_year, "score": score})

    return recommendations

## Function to that combines get_movie_properties and get_movie_recommendations
def recommend_movies(movie_id):
    movie = f"<https://triplydb.com/Triply/linkedmdb/id/film/{movie_id}>"
    properties = get_movie_properties(movie)
    similar_movies = get_movie_recommendations(properties, movie)

    print("\nSimilar Movies:")
    for i in range(len(similar_movies)):
        print(f"{i+1} - {similar_movies[i]['movie_title']} ({similar_movies[i]['movie_year']}, {similar_movies[i]['movie_director']})")
    print("\n")


print("Movie Recommender")
while (True):
    print("\nEnter a movie title:")

    movie_title = input()
    print()
    movie_list = get_movie_id(movie_title)

    if len(movie_list) > 1:
        print_movies(movie_list)
        index = "-1"
        while(not index.isnumeric() or int(index) > len(movie_list) or int(index) <= 0):
            print("\nEnter the number of the wished movie:")
            index = input()
        movie_id = movie_list[int(index) - 1]['movie_id']
        recommend_movies(movie_id)
    elif len(movie_list) == 1:
        movie_id = movie_list[0]['movie_id']
        print(f"Found movie: {movie_list[0]['movie_title']} ({movie_list[0]['movie_year']}, {movie_list[0]['movie_director']})")
        recommend_movies(movie_id)
    else:
        print("No movie found. Please try another title.")