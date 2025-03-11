import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objs as go
import streamlit as st
import polars as pl

from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import OneHotEncoder
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

if "parsed_df" not in st.session_state:
    st.session_state.parsed_df = None

# Page title
st.title("Analytics")

# Loading data
if st.session_state.parsed_df is None:
    st.info("Please upload a log file on the 'Upload' page.")
    st.stop()

data = st.session_state.parsed_df
data = data.select(["portdst","protocole","rule","action"])

##############################################
####            Preprocessing             ####
##############################################

# Encodage one-hot

encoder = OneHotEncoder(sparse_output=False)
data_encoded = encoder.fit_transform(data.to_pandas())

col_names = [
    f"{feature}_{category}" 
    for feature, categories in zip(data.columns, encoder.categories_)
    for category in categories
]

# Convertir de nouveau en DataFrame Polars
data_encoded = pl.from_pandas(pd.DataFrame(data_encoded, columns=col_names))

###############################################
####              Clustering               ####
###############################################

if st.button("Start clustering"):
    if st.session_state.parsed_df is not None:
        with st.spinner("Searching the clusters..."):
            try:

                ncp = 2
                pca = PCA(n_components=ncp)
                df_pca = pca.fit_transform(data_encoded.to_pandas())                

                cp1_var = round(pca.explained_variance_ratio_[0],3)
                cp2_var = round(pca.explained_variance_ratio_[1],3)

                # Appliquer K-Means avec k optimal choisi
                k_optimal = 2  # Par exemple, supposons que k = 3
                kmeans = KMeans(n_clusters=k_optimal, random_state=42)
                preds = kmeans.fit_predict(df_pca)
                df_pca = pl.from_pandas(pd.DataFrame(df_pca, columns=[f"Component {i+1}" for i in range(ncp)]))
                df_clust = df_pca.with_columns(pl.Series(values=preds, name='cluster_kmeans'))

                if df_clust.shape[0] > 200000: # 200k
                    perc = 200000/df_clust.shape[0]
                else:
                    perc = 1
                df_ech = pl.from_pandas(df_clust.to_pandas()
                                    .groupby("cluster_kmeans", group_keys=False)
                                    .apply(lambda x: x.sample(frac=perc, random_state=42))
                                    )

                ###############################################################
                ####              Visualisation des clusters               ####
                ###############################################################


                # Visualisation des clusters (en 2D avec PCA)
                fig = px.scatter(
                    x=df_ech.select("Component 1").to_numpy().flatten(),
                    y=df_ech.select("Component 2").to_numpy().flatten(),
                    color=df_ech.select('cluster_kmeans').to_numpy().flatten().astype(str),
                    color_discrete_map={"0": "rebeccapurple", "1": "gold"},
                    title=f'Clustering coupled with PCA ({pca.explained_variance_ratio_.sum():.3f})',
                    labels={'x': 'Component 1', 'y': 'Component 2', 'color': 'Cluster'},
                    hover_data={
                        "ip": st.session_state.parsed_df.select("ipsrc").to_numpy().flatten()
                    }
                )

                fig.update_layout(
                    xaxis_title=f'Component 1 ({cp1_var})',
                    yaxis_title=f'Component 2 ({cp2_var})'
                )
                # fig.show()
                st.plotly_chart(fig, use_container_width=True)
                
            except Exception as e:
                st.error(f"An error occured while doing the clustering : {e}")

        with st.spinner("Performing some more data analysis..."):
            try:
                data_clust = data.with_columns(pl.Series(name="cluster_kmeans", values=df_clust.select("cluster_kmeans")))
                # Analyse des variables qualitatives par cluster
                for col in data.columns : # portdst, protocole, rule, action
                    fig = make_subplots(rows=1, cols=2)

                    data_filtered = data_clust.filter(pl.col("cluster_kmeans") == 0)
                    freq_df = data_filtered.group_by(col).agg(pl.count(col).alias("frequency"))

                    fig.add_trace(
                        go.Bar(x=freq_df[col], y=freq_df['frequency'], name='Cluster 0',
                               marker=dict(color='rebeccapurple')),
                        row=1, col=1
                    )

                    data_filtered = data_clust.filter(pl.col("cluster_kmeans") == 1)
                    freq_df = data_filtered.group_by(col).agg(pl.count(col).alias("frequency"))

                    fig.add_trace(
                        go.Bar(x=freq_df[col], y=freq_df['frequency'], name='Cluster 1',
                               marker=dict(color='gold')),
                        row=1, col=2
                    )

                    fig.update_layout(
                        title=f'{col} frequencies by cluster',
                        xaxis_title='Category',
                        yaxis_title='Frequency',
                        showlegend=True
                    )
                    st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"An error occured while doing the data analysis : {e}")
    else:
        st.warning("Please parse the log file first.")