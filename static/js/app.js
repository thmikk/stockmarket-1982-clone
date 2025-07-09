class StockApp {
    constructor() {
        this.watchlist = JSON.parse(localStorage.getItem('watchlist')) || [];
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadPopularStocks();
        this.renderWatchlist();
    }

    setupEventListeners() {
        const searchInput = document.getElementById('searchInput');
        let searchTimeout;

        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            const query = e.target.value.trim();
            
            if (query.length > 1) {
                searchTimeout = setTimeout(() => {
                    this.searchStocks(query);
                }, 300);
            } else {
                this.hideSearchResults();
            }
        });

        searchInput.addEventListener('blur', () => {
            setTimeout(() => this.hideSearchResults(), 200);
        });
    }

    async loadPopularStocks() {
        const popularSymbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA'];
        const stockGrid = document.getElementById('stockGrid');
        
        stockGrid.innerHTML = '<div class="col-12 text-center"><div class="loading-spinner"></div> Loading stocks...</div>';

        try {
            const promises = popularSymbols.map(symbol => this.fetchStockData(symbol));
            const results = await Promise.allSettled(promises);
            
            stockGrid.innerHTML = '';
            
            results.forEach((result, index) => {
                if (result.status === 'fulfilled') {
                    this.renderStockCard(result.value, stockGrid);
                } else {
                    console.error(`Failed to load ${popularSymbols[index]}:`, result.reason);
                }
            });
        } catch (error) {
            stockGrid.innerHTML = '<div class="col-12 text-center text-danger">Error loading stocks</div>';
            console.error('Error loading popular stocks:', error);
        }
    }

    async fetchStockData(symbol) {
        const response = await fetch(`/api/stock/${symbol}`);
        if (!response.ok) {
            throw new Error(`Failed to fetch ${symbol}`);
        }
        return response.json();
    }

    async searchStocks(query) {
        try {
            const response = await fetch(`/api/search/${query}`);
            const results = await response.json();
            this.showSearchResults(results);
        } catch (error) {
            console.error('Search error:', error);
        }
    }

    showSearchResults(results) {
        let searchResults = document.querySelector('.search-results');
        
        if (!searchResults) {
            searchResults = document.createElement('div');
            searchResults.className = 'search-results';
            document.getElementById('searchInput').parentNode.style.position = 'relative';
            document.getElementById('searchInput').parentNode.appendChild(searchResults);
        }

        if (results.length === 0) {
            searchResults.innerHTML = '<div class="search-result-item">No results found</div>';
        } else {
            searchResults.innerHTML = results.map(stock => 
                `<div class="search-result-item" data-symbol="${stock.symbol}">
                    <strong>${stock.symbol}</strong> - ${stock.name}
                </div>`
            ).join('');

            searchResults.querySelectorAll('.search-result-item').forEach(item => {
                item.addEventListener('click', () => {
                    const symbol = item.dataset.symbol;
                    if (symbol) {
                        this.addToWatchlist(symbol);
                        this.hideSearchResults();
                        document.getElementById('searchInput').value = '';
                    }
                });
            });
        }

        searchResults.style.display = 'block';
    }

    hideSearchResults() {
        const searchResults = document.querySelector('.search-results');
        if (searchResults) {
            searchResults.style.display = 'none';
        }
    }

    renderStockCard(stock, container) {
        const changeClass = stock.change > 0 ? 'price-positive' : 
                           stock.change < 0 ? 'price-negative' : 'price-neutral';
        
        const changeIcon = stock.change > 0 ? '▲' : 
                          stock.change < 0 ? '▼' : '▬';

        const cardHtml = `
            <div class="col-md-6 col-lg-4">
                <div class="card stock-card">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <div>
                                <div class="stock-symbol">${stock.symbol}</div>
                                <div class="stock-name">${stock.name}</div>
                            </div>
                            <button class="btn btn-sm btn-outline-primary" onclick="app.addToWatchlist('${stock.symbol}')">
                                +
                            </button>
                        </div>
                        <div class="stock-price ${changeClass}">$${stock.price.toFixed(2)}</div>
                        <div class="d-flex justify-content-between align-items-center">
                            <span class="badge ${changeClass === 'price-positive' ? 'bg-success' : 
                                              changeClass === 'price-negative' ? 'bg-danger' : 'bg-secondary'} change-badge">
                                ${changeIcon} ${stock.change >= 0 ? '+' : ''}${stock.change.toFixed(2)} 
                                (${stock.changePercent >= 0 ? '+' : ''}${stock.changePercent.toFixed(2)}%)
                            </span>
                            <small class="text-muted">Vol: ${this.formatNumber(stock.volume)}</small>
                        </div>
                    </div>
                </div>
            </div>
        `;

        container.innerHTML += cardHtml;
    }

    addToWatchlist(symbol) {
        if (!this.watchlist.includes(symbol)) {
            this.watchlist.push(symbol);
            localStorage.setItem('watchlist', JSON.stringify(this.watchlist));
            this.renderWatchlist();
        }
    }

    removeFromWatchlist(symbol) {
        this.watchlist = this.watchlist.filter(s => s !== symbol);
        localStorage.setItem('watchlist', JSON.stringify(this.watchlist));
        this.renderWatchlist();
    }

    async renderWatchlist() {
        const watchlistElement = document.getElementById('watchlist');
        
        if (this.watchlist.length === 0) {
            watchlistElement.innerHTML = '<p class="text-muted">Add stocks to your watchlist</p>';
            return;
        }

        watchlistElement.innerHTML = '<div class="loading-spinner"></div> Loading watchlist...';

        try {
            const promises = this.watchlist.map(symbol => this.fetchStockData(symbol));
            const results = await Promise.allSettled(promises);
            
            let html = '';
            results.forEach((result, index) => {
                if (result.status === 'fulfilled') {
                    const stock = result.value;
                    const changeClass = stock.change > 0 ? 'text-success' : 
                                       stock.change < 0 ? 'text-danger' : 'text-muted';
                    
                    html += `
                        <div class="d-flex justify-content-between align-items-center mb-2 p-2 border rounded">
                            <div>
                                <strong>${stock.symbol}</strong>
                                <div class="small ${changeClass}">
                                    $${stock.price.toFixed(2)} (${stock.changePercent >= 0 ? '+' : ''}${stock.changePercent.toFixed(2)}%)
                                </div>
                            </div>
                            <button class="btn btn-sm btn-outline-danger" onclick="app.removeFromWatchlist('${stock.symbol}')">
                                ×
                            </button>
                        </div>
                    `;
                }
            });
            
            watchlistElement.innerHTML = html;
        } catch (error) {
            watchlistElement.innerHTML = '<div class="text-danger">Error loading watchlist</div>';
            console.error('Error loading watchlist:', error);
        }
    }

    formatNumber(num) {
        if (num >= 1000000000) {
            return (num / 1000000000).toFixed(1) + 'B';
        }
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        }
        if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }
}

// Initialize the app when the page loads
const app = new StockApp();
