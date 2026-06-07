"""Autenticación Fluxa — login con usuario y contraseña."""

from __future__ import annotations

import streamlit as st

# Credenciales (contraseña hasheada con bcrypt)
_CREDENTIALS = {
    "albaguerra": {
        "name": "Alba Guerra",
        "password_hash": "$2b$12$tOjZJAfsZfD0pVX5fMp/r.0Aqvx39oukOaOtY2ZUt0m5nzk43u6FC",
    }
}

_LOGIN_CSS = """
<style>
.login-wrap {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #07070f;
}
.login-box {
  width: 100%;
  max-width: 400px;
  background: #0d0d1a;
  border-radius: 24px;
  padding: 3rem 2.5rem;
  box-shadow: 0 0 0 1px rgba(255,255,255,0.04),
              0 24px 64px rgba(0,0,0,0.6);
}
.login-logo {
  text-align: center;
  font-size: 2rem;
  font-weight: 900;
  color: #f0f0f8;
  letter-spacing: -0.04em;
  font-family: 'Inter', sans-serif;
  margin-bottom: 0.3rem;
}
.login-sub {
  text-align: center;
  font-size: 0.82rem;
  color: #2a2a42;
  font-family: 'Inter', sans-serif;
  margin-bottom: 2.5rem;
}
</style>
"""


def check_login() -> bool:
    """
    Muestra la pantalla de login si el usuario no está autenticado.
    Retorna True si el usuario ya está logueado.
    """
    import bcrypt

    if st.session_state.get("_auth_ok"):
        return True

    st.markdown(_LOGIN_CSS, unsafe_allow_html=True)

    # Centrar el formulario
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("""
        <div class="login-logo">⚡ fluxa</div>
        <div class="login-sub">Suite de lanzamiento · COD Colombia</div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            usuario = st.text_input("Usuario", placeholder="albaguerra")
            password = st.text_input("Contraseña", type="password", placeholder="••••••••••")
            submit = st.form_submit_button("Entrar", use_container_width=True, type="primary")

        if submit:
            cred = _CREDENTIALS.get(usuario.strip().lower())
            if cred and bcrypt.checkpw(password.encode(),
                                       cred["password_hash"].encode()):
                st.session_state["_auth_ok"] = True
                st.session_state["_auth_name"] = cred["name"]
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")

    return False
