"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.HashA2aNode = void 0;
const OPERATIONS = [
    {
        value: 'getPrice',
        description: 'Multi-oracle price for any asset (BTC, ETH, SOL, etc.)',
        endpoint: '/api/v1/feeds/prices',
        method: 'POST',
    },
    {
        value: 'listAssets',
        description: 'List all 36 supported assets with metadata',
        endpoint: '/api/v1/feeds/prices',
        method: 'POST',
    },
    {
        value: 'scanArbitrage',
        description: 'Cross-oracle arbitrage scan across all assets',
        endpoint: '/api/v1/feeds/arbitrage',
        method: 'POST',
    },
    {
        value: 'deepResearch',
        description: 'Full web + news + AI research on any topic',
        endpoint: '/api/v1/research',
        method: 'POST',
    },
    {
        value: 'getMarketData',
        description: 'Prediction market data from Polymarket, Kalshi, PredictIt, Manifold',
        endpoint: '/api/v1/requests',
        method: 'POST',
    },
    {
        value: 'aggregateMarketData',
        description: 'Multi-provider intelligence aggregation',
        endpoint: '/api/v1/requests/aggregate',
        method: 'POST',
    },
];
class HashA2aNode {
    constructor() {
        this.description = {
            displayName: 'HashA2A',
            name: 'hasha2a',
            icon: 'file:hasha2a.svg',
            group: ['transform'],
            version: 1,
            subtitle: '={{$parameter["operation"]}}',
            description: 'Get multi-oracle prices, arbitrage signals, prediction data, and AI research',
            defaults: {
                name: 'HashA2A',
            },
            inputs: ['main'],
            outputs: ['main'],
            credentials: [
                {
                    name: 'hasha2aApi',
                    required: true,
                },
            ],
            properties: [
                {
                    displayName: 'Operation',
                    name: 'operation',
                    type: 'options',
                    noDataExpression: true,
                    options: OPERATIONS.map((op) => ({
                        name: op.value
                            .replace(/([A-Z])/g, ' $1')
                            .replace(/^./, (s) => s.toUpperCase())
                            .trim(),
                        value: op.value,
                        description: op.description,
                    })),
                    default: 'getPrice',
                },
                {
                    displayName: 'Asset',
                    name: 'asset',
                    type: 'string',
                    default: 'BTC/USD',
                    placeholder: 'BTC/USD',
                    description: 'Asset symbol (e.g. BTC/USD, ETH/USD, SOL/USD, HBAR/USD)',
                    displayOptions: {
                        show: { operation: ['getPrice', 'listAssets'] },
                    },
                },
                {
                    displayName: 'Query / Topic',
                    name: 'query',
                    type: 'string',
                    default: '',
                    placeholder: 'What is the prediction for the next Fed rate decision?',
                    description: 'Research topic or prediction market query',
                    displayOptions: {
                        show: { operation: ['deepResearch', 'getMarketData'] },
                    },
                },
                {
                    displayName: 'Provider',
                    name: 'provider',
                    type: 'options',
                    options: [
                        { name: 'Polymarket', value: 'polymarket' },
                        { name: 'Kalshi', value: 'kalshi' },
                        { name: 'PredictIt', value: 'predictit' },
                        { name: 'Manifold', value: 'manifold' },
                        { name: 'All Providers', value: 'all' },
                    ],
                    default: 'all',
                    description: 'Prediction market provider to query',
                    displayOptions: {
                        show: { operation: ['getMarketData', 'aggregateMarketData'] },
                    },
                },
                {
                    displayName: 'Max Providers',
                    name: 'maxProviders',
                    type: 'number',
                    default: 4,
                    description: 'Maximum number of providers to aggregate',
                    displayOptions: {
                        show: { operation: ['aggregateMarketData'] },
                    },
                },
                {
                    displayName: 'Timeout (seconds)',
                    name: 'timeout',
                    type: 'number',
                    default: 30,
                    description: 'Timeout for the request in seconds',
                },
                {
                    displayName: 'Additional Options',
                    name: 'additionalOptions',
                    type: 'collection',
                    placeholder: 'Add Option',
                    default: {},
                    options: [
                        {
                            displayName: 'Include AI Analysis',
                            name: 'includeAI',
                            type: 'boolean',
                            default: false,
                            description: 'Whether to include AI-powered analysis of the data',
                        },
                        {
                            displayName: 'Raw Response',
                            name: 'raw',
                            type: 'boolean',
                            default: false,
                            description: 'Return raw response instead of parsed JSON',
                        },
                    ],
                },
            ],
        };
    }
    async execute() {
        const items = this.getInputData();
        const returnData = [];
        const credentials = await this.getCredentials('hasha2aApi');
        const serverUrl = credentials.serverUrl.replace(/\/+$/, '');
        for (let i = 0; i < items.length; i++) {
            try {
                const operation = this.getNodeParameter('operation', i);
                const opConfig = OPERATIONS.find((o) => o.value === operation);
                const additional = this.getNodeParameter('additionalOptions', i, {});
                const url = `${serverUrl}${opConfig.endpoint}`;
                const headers = {
                    'Content-Type': 'application/json',
                    Accept: 'application/json',
                };
                if (credentials.apiKey) {
                    headers['Authorization'] = `Bearer ${credentials.apiKey}`;
                }
                const timeout = this.getNodeParameter('timeout', i, 30);
                let body = {};
                switch (operation) {
                    case 'getPrice': {
                        const asset = this.getNodeParameter('asset', i);
                        body = { asset };
                        if (additional.includeAI)
                            body.analyze = true;
                        break;
                    }
                    case 'listAssets': {
                        body = {};
                        break;
                    }
                    case 'scanArbitrage': {
                        body = {};
                        break;
                    }
                    case 'deepResearch': {
                        const query = this.getNodeParameter('query', i);
                        body = { query };
                        break;
                    }
                    case 'getMarketData': {
                        const query = this.getNodeParameter('query', i);
                        const provider = this.getNodeParameter('provider', i);
                        body = { query, provider: provider === 'all' ? undefined : provider };
                        break;
                    }
                    case 'aggregateMarketData': {
                        const query = this.getNodeParameter('query', i);
                        const provider = this.getNodeParameter('provider', i);
                        const maxProviders = this.getNodeParameter('maxProviders', i, 4);
                        body = { query, provider: provider === 'all' ? undefined : provider, max_providers: maxProviders };
                        break;
                    }
                }
                const response = await this.helpers.httpRequest({
                    method: opConfig.method,
                    url,
                    headers,
                    body: opConfig.method === 'POST' ? body : undefined,
                    qs: opConfig.method === 'GET' ? body : undefined,
                    json: true,
                    timeout: timeout * 1000,
                });
                returnData.push({
                    json: additional.raw ? response : {
                        operation,
                        data: response,
                        timestamp: Date.now(),
                    },
                });
            }
            catch (error) {
                if (this.continueOnFail()) {
                    returnData.push({
                        json: {
                            error: error.message,
                            operation: this.getNodeParameter('operation', i),
                        },
                    });
                    continue;
                }
                throw error;
            }
        }
        return this.prepareOutputData(returnData);
    }
}
exports.HashA2aNode = HashA2aNode;
//# sourceMappingURL=HashA2aNode.node.js.map