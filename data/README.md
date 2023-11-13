# Data

- **imdb_recs_raw.csv**: IMDB's top 250 movies and 12 recommended movies for each of the source movies.
- **imdb_recs_availability.csv**: A binary matrix that can be applied to imdb_recs_raw to filter out movies that are not available on triplydb.
- **available_src_movies.csv**: A list containing all of IMDb's top 250 movies, that are also available on triplydb together with all their recommendations. We can make recommendations for these movies and evaluate them on the recommendations of IMDb.