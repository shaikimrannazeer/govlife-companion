from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.smart_alerts import collect_smart_alerts
from utils.translations import t


def render(user: dict) -> None:
    st.title(t("smart_alerts"))
    alerts = collect_smart_alerts(user)
    for alert in alerts:
        message = f"**{alert['Area']}**: {alert['Message']}"
        if alert["Level"] == "Danger":
            st.error(message)
        elif alert["Level"] == "Warning":
            st.warning(message)
        elif alert["Level"] == "Good":
            st.success(message)
        else:
            st.info(message)
    st.dataframe(pd.DataFrame(alerts), use_container_width=True, hide_index=True)

