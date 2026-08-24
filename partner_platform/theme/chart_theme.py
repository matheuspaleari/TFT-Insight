def apply_chart_theme(
    figure,
    *,
    height: int = 360,
):
    figure.update_layout(
        height=height,
        margin=dict(
            l=8,
            r=8,
            t=16,
            b=8,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            color="#94A1B5",
        ),
        hoverlabel=dict(
            bgcolor="#111722",
            bordercolor="#253044",
            font_color="#F4F7FB",
        ),
    )

    figure.update_xaxes(
        showgrid=False,
        zeroline=False,
        color="#7F8DA3",
    )

    figure.update_yaxes(
        gridcolor="rgba(255,255,255,.045)",
        zeroline=False,
        color="#7F8DA3",
    )

    return figure
