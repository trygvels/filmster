import dash
from dash import dcc, html
import dash.dash_table as dash_table
from dash.dependencies import Input, Output, State
import pandas as pd

# df = pd.read_csv('ratings.csv')
df = pd.read_parquet("ratings_filtered.parquet")

genres = set()
for genre_string in df["Genres"].dropna():
    for genre in genre_string.split(", "):
        genres.add(genre)
genres = sorted(list(genres))

app = dash.Dash(__name__, external_stylesheets=["https://fonts.googleapis.com/css2?family=Roboto&display=swap"])

server = app.server
app.layout = html.Div(
    [
        html.Div(
            [
                html.Img(
                    id="background-image",
                    src="/assets/pixel_art_tv.png",
                    className="background-image"
                ),
                html.Div(
                    "TRYBEKKAS \n FILMVELGER",
                    className="title"
                ),
                html.Div(
                    id="output-container",
                    className="output-content",  
                ),
            ],
            className="main-div",
        ),
        html.Div(
            [
                html.Button("Velg film", id="submit-button", n_clicks=0, className="button"),
                html.Button("Vis alternativer", id="show-button", n_clicks=0, className="button"),
                html.Label("Type:", className="label"),
                dcc.Dropdown(id="type-filter", options=[{"label": "Film", "value": "Movie"}, {"label": "TV-serie", "value": "TV-serie"}], value="Movie"),
                html.Label("Genres:", className="label"),
                dcc.Dropdown(id="genre-filter", options=[{"label": genre, "value": genre} for genre in genres], multi=True),
                html.Label("Year:", className="label"),
                dcc.RangeSlider(
                    id="year-filter", min=df["Year"].min(), max=df["Year"].max(), marks=None, step=1, tooltip={"placement": "bottom", "always_visible": True}
                ),
                html.Label("Trygves rating:", className="label"),
                dcc.RangeSlider(
                    id="your-rating-filter", min=1, max=10, tooltip={"placement": "bottom", "always_visible": True}, value=[9, 10], step=0.1, marks=None
                ),
                html.Label("IMDb rating:", className="label"),
                dcc.RangeSlider(
                    id="imdb-rating-filter", min=1, max=10, tooltip={"placement": "bottom", "always_visible": True}, value=[7.5, 10], step=0.1, marks=None
                ),
                html.Label("Runtime:", className="label"),
                dcc.RangeSlider(
                    id="runtime-filter",
                    min=df[df["Title Type"] == "movie"]["Runtime (mins)"].min(),
                    max=df[df["Title Type"] == "movie"]["Runtime (mins)"].max(),
                    tooltip={"placement": "bottom", "always_visible": True},
                    step=1,
                    marks=None,
                ),
            ],
            className="controls",
        ),
        html.Div(id="table-container"),
    ],
    className="layout",
)


# Make this div have a white background and a strong black border


@app.callback(
    Output("table-container", "children"),
    [
        Input("genre-filter", "value"),
        Input("year-filter", "value"),
        Input("your-rating-filter", "value"),
        Input("imdb-rating-filter", "value"),
        Input("runtime-filter", "value"),
        Input("type-filter", "value"),
        Input("show-button", "n_clicks"),
    ],
)
def update_table(genres, years, your_ratings, imdb_ratings, runtime, type_filter, n):
    if n > 0:
        dff = df
        if genres:
            dff = dff[dff["Genres"].apply(lambda x: any(genre in x for genre in genres))]
        if years:
            dff = dff[(dff["Year"] >= years[0]) & (dff["Year"] <= years[1])]
        if your_ratings:
            dff = dff[(dff["Your Rating"] >= your_ratings[0]) & (dff["Your Rating"] <= your_ratings[1])]
        if imdb_ratings:
            dff = dff[(dff["IMDb Rating"] >= imdb_ratings[0]) & (dff["IMDb Rating"] <= imdb_ratings[1])]
        if runtime:
            dff = dff[(dff["Runtime (mins)"] >= runtime[0]) & (dff["Runtime (mins)"] <= runtime[1])]
        if type_filter == "Movie":
            dff = dff[dff["Title Type"] == "movie"]
        elif type_filter == "TV-serie":
            dff = dff[dff["Title Type"].isin(["tvSeries", "tvMiniSeries"])]

        # convert types of dff coluns Streaming and Buy to string
        dff["streaming"] = dff["streaming"].astype(str)
        dff["buy"] = dff["buy"].astype(str)

        # rename column "Your Rating" to "Trygves Rating"
        dff = dff.rename(columns={"Your Rating": "Trygves Rating"})

        cols = [{"name": i, "id": i} for i in dff.columns]
        # drop columns "Date Rated", "Const", "Num Votes" and "Release Date"
        cols = [col for col in cols if col["id"] not in ["Date Rated", "Const", "Num Votes", "Release Date"]]
        # rename column "Your Rating" to "Trygves Rating"
        return dash_table.DataTable(
            id="table",
            columns=cols,
            data=dff.to_dict("records"),
        )
    return None

@app.callback(
    Output("output-container", "children"),
    [Input("submit-button", "n_clicks")],
    [
        State("genre-filter", "value"),
        State("year-filter", "value"),
        State("your-rating-filter", "value"),
        State("imdb-rating-filter", "value"),
        State("runtime-filter", "value"),
        State("type-filter", "value"),
    ],
)
def update_output(n_clicks, genres, years, your_ratings, imdb_ratings, runtime, type_filter):
    if n_clicks > 0:
        dff = df
        if genres:
            dff = dff[dff["Genres"].apply(lambda x: any(genre in x for genre in genres))]
        if years:
            dff = dff[(dff["Year"] >= years[0]) & (dff["Year"] <= years[1])]
        if your_ratings:
            dff = dff[(dff["Your Rating"] >= your_ratings[0]) & (dff["Your Rating"] <= your_ratings[1])]
        if imdb_ratings:
            dff = dff[(dff["IMDb Rating"] >= imdb_ratings[0]) & (dff["IMDb Rating"] <= imdb_ratings[1])]
        if type_filter == "Movie":
            dff = dff[dff["Title Type"] == "movie"]
            if runtime:
                dff = dff[(dff["Runtime (mins)"] >= runtime[0]) & (dff["Runtime (mins)"] <= runtime[1])]
        elif type_filter == "TV-serie":
            dff = dff[dff["Title Type"].isin(["tvSeries", "tvMiniSeries"])]

        if not dff.empty:
            selected_movie = dff.sample(n=1).iloc[0]
            streaming_ = list(selected_movie["streaming"])
            buy_ = list(selected_movie["buy"])

            if streaming_:
                streaming = ", ".join(streaming_)
                streaming_color = "available"
            else:
                streaming = "Ikke tilgjengelig for strømming"
                streaming_color = "unavailable"

            if buy_:
                buy = ", ".join(buy_)
                buy_color = "available"
            else:
                buy = "Ikke tilgjengelig for Leie/Kjøp"
                buy_color = "unavailable"

            description = selected_movie["description"]
            # if description is too long, cut it off and add "..."
            if len(description) > 500:
                description = description[:500] + "..."

            return html.Div(
                [
                    html.P(f"{selected_movie['Title']} ({selected_movie['Year']})", className="movie-title"),
                    html.Div(
                        [
                            html.Img(src=selected_movie["thumbnail"], alt="Cover art", className="cover-art"),
                            html.Div(
                                [
                                    html.P(
                                        f"{int(selected_movie['Runtime (mins)'])} min. Directed by {selected_movie['Directors']}. [{selected_movie['Genres']}]", 
                                        className="movie-details"
                                    ),
                                    html.P(f"Strømming: {streaming}", className=streaming_color),
                                    html.P(f"Lei/Kjøp: {buy}", className=buy_color),
                                    html.P(
                                        description, 
                                        className="movie-description",
                                    ),
                                    
                                ],
                                className="description-container",
                            ),
                        ],
                        className="content-flex",
                    ),
                ],
            )
    return None



if __name__ == "__main__":
    app.run_server(debug=True)
