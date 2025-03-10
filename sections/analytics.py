import pandas as pd
import plotly.express as px
import streamlit as st
import polars as pl

from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import OneHotEncoder
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering

if "parsed_df" not in st.session_state:
    st.session_state.parsed_df = None

# Page title
st.title("Analytiques")

# Loading data
if st.session_state.parsed_df is None:
    st.info("Please upload a log file on the 'Upload' page.")
    st.stop()

data = st.session_state.parsed_df
data = data.select(["portdest","protocole","regle1","status"])

# Sélectionner toutes les colonnes numériques
quanti = data.select(pl.col(pl.Int64))

# Sélectionner toutes les colonnes de type chaîne
quali = data.select(pl.col(pl.String))

##############################################
####            Preprocessing             ####
##############################################

# Normalisation des données quanti (Standardisation : moyenne = 0, écart-type = 1)

scaler = StandardScaler()
data_quanti = scaler.fit_transform(quanti.to_pandas())

# Convertir de nouveau en DataFrame Polars
data_quanti = pl.from_pandas(pd.DataFrame(data_quanti, columns=quanti.columns))

# Encodage one-hot des données quali

encoder = OneHotEncoder(sparse_output=False)
data_quali = encoder.fit_transform(quali.to_pandas())

col_names = [
    f"{feature}_{category}" 
    for feature, categories in zip(quali.columns, encoder.categories_)
    for category in categories
]

# Convertir de nouveau en DataFrame Polars
data_quali = pl.from_pandas(pd.DataFrame(data_quali, columns=col_names))

df = pl.concat([data_quanti, data_quali], how="horizontal")

###############################################
####              Clustering               ####
###############################################

if st.button("Start clustering"):
    if st.session_state.parsed_df is not None:
        with st.spinner("Searching the clusters..."):
            try:
                # Appliquer K-Means avec k optimal choisi
                k_optimal = 2  # Par exemple, supposons que k = 3
                kmeans = KMeans(n_clusters=k_optimal, random_state=42)
                preds = kmeans.fit_predict(df.to_pandas())
                df = df.with_columns(pl.Series(values=preds, name='cluster_kmeans'))


                # dbscan = DBSCAN(eps=0.5, min_samples=10)
                # preds = dbscan.fit_predict(df.to_pandas())
                # df = df.with_columns(pl.Series(values=preds, name='cluster_dbscan'))

                # agg_clustering = AgglomerativeClustering(n_clusters=2)
                # preds = agg_clustering.fit_predict(df.to_pandas())
                # df = df.with_columns(pl.Series(values=preds, name='cluster_agg'))                

                ###############################################################
                ####              Visualisation des clusters               ####
                ###############################################################


                # Visualisation des clusters (en 2D avec PCA)
                from sklearn.decomposition import PCA

                pca = PCA(n_components=2)
                df_pca = pca.fit_transform(df.to_pandas())

                fig = px.scatter(
                    x=df_pca[:, 0],
                    y=df_pca[:, 1],
                    color=df['cluster_kmeans'],
                    color_continuous_scale='viridis',
                    title='Clustering coupled with PCA',
                    labels={'x': 'Component 1', 'y': 'Component 2', 'color': 'Cluster'},
                )

                fig.update_layout(
                    xaxis_title='Component 1',
                    yaxis_title='Component 2'
                )

                # fig.show()
                st.plotly_chart(fig, use_container_width=True)
                
            except Exception as e:
                st.error(f"An error occured : {e}")
    else:
        st.warning("Please parse the log file first.")

# Choisir le nombre de clusters (méthode du coude)
# inertia = []
# for k in range(1, 11):
#     kmeans = KMeans(n_clusters=k, random_state=42)
#     kmeans.fit(df_scaled.to_pandas())
#     inertia.append(kmeans.inertia_)

# # Tracer la courbe pour la méthode du coude
# plt.plot(range(1, 11), inertia, marker='o')
# plt.title('Méthode du coude')
# plt.xlabel('Nombre de clusters')
# plt.ylabel('Inertie')
# plt.show()

