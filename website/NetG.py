def find_word_in_list(words, word_list):
    # Convert the target word to lowercase for case-insensitive comparison
    indices = []
    for word in words:
        word = word.lower()    
        # Create an empty list to store indices of matching elements
        # Iterate through the list and check each element
        for index, element in enumerate(word_list):
            # Convert the element to lowercase for case-insensitive comparison
            element_lower = element.lower()        
            if word in element_lower:
                indices.append(index)
    return indices


def NetWorkGrap(dfTemp, search_keyword,Headers,gs):
    import networkx as nx
    import plotly.graph_objects as go
    # Create a graph
    G = nx.Graph()
    # Add the central node (search keyword)
    G.add_node(search_keyword)
    # Add nodes (paper titles, authors, and journals) and edges
    if gs == 'gs':
        for dic in dfTemp:
            Org_paper_title = dic[Headers[0]] 
            relPaper = dic[Headers[1]] 
            authors = dic[Headers[2]]
            Citations = dic[Headers[3]]
            if authors != "NA":
                # Add nodes for paper title, authors, and journal
                G.add_node(Org_paper_title)
                G.add_node(relPaper)
                G.add_node(authors)
                G.add_node(Citations)
                # Add edges connecting the central node to paper title, authors, and journal
                G.add_edge(search_keyword, Org_paper_title)
                G.add_edge(Org_paper_title, relPaper)
                G.add_edge(relPaper, authors)
                G.add_edge(relPaper, Citations)
    elif gs =='pm':
        for dic in dfTemp:
            paper_title = dic[Headers[0]] # paper title
            authors = dic[Headers[1]] # authors 
            journal = dic[Headers[2]] # journal
            if authors != "NA":
                # Add nodes for paper title, authors, and journal
                G.add_node(paper_title)
                G.add_node(authors)
                G.add_node(journal)
                # Add edges connecting the central node to paper title, authors, and journal
                G.add_edge(search_keyword, journal)
                G.add_edge(journal, authors)
                G.add_edge(journal, paper_title)
    elif gs =='ai':
        for dic in dfTemp:
            Org_paper_title = dic[Headers[0]] 
            relPaper = dic[Headers[1]] 
            authors = dic[Headers[2]]
            Journal = dic[Headers[3]]
            if authors != "NA":
                # Add nodes for paper title, authors, and journal
                G.add_node(Org_paper_title)
                G.add_node(relPaper)
                G.add_node(authors)
                G.add_node(Journal)
                # Add edges connecting the central node to paper title, authors, and journal
                G.add_edge(search_keyword, Org_paper_title)
                G.add_edge(Org_paper_title, relPaper)
                G.add_edge(relPaper, authors)
                G.add_edge(relPaper, Journal)  
    

    # Create a Plotly figure
    pos = nx.spring_layout(G, seed=60)  # Seed for reproducibility
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=1, color='lightgray'),  # Decrease line width and change color
        hoverinfo='none',
        mode='lines')

    node_x = []
    node_y = []
    node_text_full = []  # Store full text for hover
    node_text_short = []  # Store shortened text for display
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        full_text = node
        short_text = node[:20] + '...' if len(node) > 65 else node
        node_text_full.append(full_text)
        node_text_short.append(short_text)

    node_trace = go.Scatter(
    x=node_x,
    y=node_y,
    mode='markers+text',
    marker=dict(
    showscale=False,
    color='skyblue',
    opacity=0.45,
    size=25,  # Increase the node size
    line=dict(width=2, color='darkblue')
    ),
    text=node_text_short,
    hoverinfo='none',  # Hide default hover info
    hovertemplate='%{customdata}',  # Use customdata for full text in the hover tooltip
    customdata=node_text_full,  # Store full text in customdata
    textfont=dict(size=15, color='black'),
    textposition='bottom center'
)
    
    fig = go.Figure(data=[edge_trace, node_trace],
                layout=go.Layout(
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=0, l=0, r=0, t=0),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    plot_bgcolor='white',
                    # width="100%",  # Set width to 100% for responsiveness
                    # height="100%",  # Set height to 100% for responsiveness
                ))
    # Update figure layout for better appearance
    fig.update_layout(
    autosize=True,  # Enable responsive mode
    clickmode='event+select',  # Set click mode
    hoverdistance=20,  # Set hover distance
    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),  # Customize x-axis
    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),  # Customize y-axis
    showlegend=False,  # Hide legend
    margin=dict(b=0, l=0, r=0, t=0),  # Set margins
    plot_bgcolor='white',  # Set plot background color
    )
    fig.update_traces(orientation='v')  # Horizontal bars
    # Add interactivity for dragging and zooming
    fig.update_xaxes(
        showgrid=False,
        showline=False,
        zeroline=False,
        showticklabels=False
    )
    # Add custom CSS styles for improved visuals and interactions
    fig.update_layout(
        template="plotly_white",  # Use "plotly_white" template
    )
    # fig.show(config={'responsive': True, 'scrollZoom': True, 'displayModeBar': False})
    # Add JavaScript code for node click interactions
    # Convert the Plotly figure to an HTML-compatible format with custom CSS and JavaScript
    graph_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
    # Display or save the HTML
    return graph_html