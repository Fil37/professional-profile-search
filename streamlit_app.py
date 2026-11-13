"""Streamlit interface for searching public professional profiles."""

import streamlit as st

from workflow import run_search


st.set_page_config(page_title="Recherche de profils publics", page_icon="🔎")
st.title("Recherche de profils professionnels publics")
st.caption(
    "Les résultats proviennent de moteurs de recherche publics. "
    "Ils ne confirment pas à eux seuls l'identité d'une personne."
)

request = st.text_area(
    "Décrivez la personne recherchée",
    placeholder="Ex. Franck Essome, ingénieur chez BNBXTECH à Orsay, France",
)

if st.button("Rechercher", type="primary"):
    if not request.strip():
        st.warning("Saisissez une demande de recherche.")
    else:
        try:
            result = run_search(request)
        except Exception as error:
            st.error(f"La recherche n'a pas pu aboutir : {error}")
        else:
            criteria = result["criteria"]
            st.subheader("Critères extraits")
            st.json(criteria.model_dump(exclude_none=True))

            if not criteria.name.strip():
                st.warning(
                    "Le nom n'a pas été extrait. Précisez-le puis réessayez."
                )
            else:
                outcome = result["outcome"]
                if outcome.candidates:
                    st.subheader("Profils candidats")
                    for candidate in outcome.candidates:
                        with st.container(border=True):
                            st.markdown(f"### [{candidate.title or candidate.url}]({candidate.url})")
                            st.write(f"Correspondance : **{candidate.match_score}/100**")
                            st.write(f"Source(s) : {', '.join(candidate.sources)}")
                            if candidate.matched_fields:
                                st.write(
                                    "Critères corroborés : "
                                    + ", ".join(candidate.matched_fields)
                                )
                            if candidate.unknown_fields:
                                st.write(
                                    "Critères non vérifiés : "
                                    + ", ".join(candidate.unknown_fields)
                                )
                            if candidate.snippet:
                                st.caption(candidate.snippet)
                else:
                    st.info(
                        "Aucun profil candidat exploitable n'a été trouvé. "
                        "Cela ne prouve pas qu'aucun profil n'existe."
                    )

                for message in outcome.provider_errors:
                    st.warning(message)
                for message in outcome.skipped_providers:
                    st.caption(message)
