# Excuse Email Draft Tool

A modern web application that generates professional excuse emails using AI-powered language models via Databricks Model Serving. Built with FastAPI backend and React frontend, designed to work locally and deploy seamlessly to Databricks Apps.

## Features

- **AI-Powered Email Generation**: Uses Databricks Model Serving LLM to generate contextually appropriate excuse emails
- **Customizable Options**: Choose from multiple categories, tones, and seriousness levels
- **Modern UI**: Clean, responsive design built with React and Tailwind CSS
- **Professional Output**: Generates both subject lines and complete email bodies
- **Copy to Clipboard**: Easy copying of generated emails
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Health Monitoring**: Multiple health check endpoints for production monitoring

## Project Structure

```
excuse-gen-app/
├── app.yaml                    # Databricks Apps configuration
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git ignore patterns
├── README.md                   # This documentation
├── src/
│   └── app.py                 # FastAPI backend application
└── public/
    └── index.html             # Single-page React frontend
```

## Quick Start

### Prerequisites

- Python 3.8+
- Databricks workspace with Model Serving endpoint
- Databricks personal access token

### Local Development

1. **Clone and setup the project:**
   ```bash
   cd excuse-gen-app
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your credentials:
   ```env
   DATABRICKS_API_TOKEN=your_databricks_personal_access_token
   DATABRICKS_ENDPOINT_URL=https://dbc-32cf6ae7-cf82.staging.cloud.databricks.com/serving-endpoints/databricks-gpt-oss-120b/invocations
   PORT=8000
   HOST=0.0.0.0
   ```

3. **Run the application:**
   ```bash
   python -m uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Access the application:**
   Open your browser to `http://localhost:8000`

### Databricks Apps Deployment

1. **Configure App Secret:**
   In your Databricks workspace, create an App secret with key `databricks_token` containing your personal access token.

2. **Deploy the application:**
   ```bash
   databricks apps deploy excuse-gen-app --source-code-path /path/to/excuse-gen-app
   ```

3. **Access your deployed app:**
   The app will be available at the URL provided by Databricks Apps.

## API Endpoints

### Main Endpoints

- `POST /api/generate-excuse` - Generate excuse email
- `GET /` - Serve React frontend

### Health & Monitoring

- `GET /health` - Application health check
- `GET /healthz` - Kubernetes-style health check
- `GET /ready` - Readiness check
- `GET /ping` - Simple ping endpoint
- `GET /metrics` - Prometheus-style metrics
- `GET /debug` - Debug information

## Usage Guide

### Form Configuration

1. **Category**: Select from predefined categories:
   - Running Late
   - Missed Meeting
   - Deadline
   - WFH/OOO
   - Social
   - Travel

2. **Tone**: Choose the email tone:
   - Sincere: Professional and apologetic
   - Playful: Light-hearted and humorous
   - Corporate: Formal business communication

3. **Seriousness Level**: Adjust from 1 (very silly) to 5 (serious)

4. **Required Fields**:
   - Recipient Name
   - Sender Name
   - ETA/When (timeframe or deadline)

### Generated Output

The application generates:
- **Subject Line**: Contextually appropriate email subject
- **Email Body**: Complete email with:
  - Professional greeting
  - Apology/excuse explanation
  - Reason or context
  - Next steps or resolution
  - Professional sign-off

## Technical Details

### Backend (FastAPI)

- **Framework**: FastAPI with async/await support
- **CORS**: Configured for cross-origin requests
- **Logging**: Comprehensive request/response logging
- **Error Handling**: Graceful error handling with meaningful messages
- **LLM Integration**: Async HTTP calls to Databricks Model Serving

### Frontend (React)

- **Framework**: React 18 with hooks
- **Styling**: Tailwind CSS via CDN
- **State Management**: React hooks for form and application state
- **Responsive Design**: Mobile-first approach with responsive grid
- **User Experience**: Loading states, error handling, success feedback

### LLM Integration

The application integrates with Databricks Model Serving using structured prompts that generate JSON responses:

```json
{
  "subject": "Running Late - ETA 15 minutes",
  "body": "Dear Alex,\n\nI wanted to let you know...\n\nBest regards,\nMona"
}
```

**Prompt Engineering Features**:
- Context-aware generation based on category, tone, and seriousness
- Structured email format with proper greeting, body, and sign-off
- Fallback parsing for different response formats
- Error handling for malformed responses

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABRICKS_API_TOKEN` | Personal access token for Databricks | Yes |
| `DATABRICKS_ENDPOINT_URL` | Model serving endpoint URL | Yes |
| `PORT` | Application port (default: 8000) | No |
| `HOST` | Application host (default: 0.0.0.0) | No |

### Databricks Apps Configuration

The `app.yaml` file configures the Databricks Apps deployment:

```yaml
command: [
  "uvicorn",
  "src.app:app",
  "--host", "0.0.0.0",
  "--port", "8000"
]

env:
  - name: 'DATABRICKS_API_TOKEN'
    valueFrom: databricks_token  # References App secret
  - name: 'DATABRICKS_ENDPOINT_URL'
    value: "https://dbc-32cf6ae7-cf82.staging.cloud.databricks.com/serving-endpoints/databricks-gpt-oss-120b/invocations"
  - name: 'PORT'
    value: "8000"
  - name: 'HOST'
    value: "0.0.0.0"
```

## Troubleshooting

### Common Issues

1. **"DATABRICKS_API_TOKEN not configured"**
   - Ensure your `.env` file has the correct token
   - For Databricks Apps, verify the App secret is configured

2. **"Public directory not found"**
   - Ensure the `public/` directory exists with `index.html`
   - Check file permissions

3. **"Timeout calling Databricks API"**
   - Verify your Databricks endpoint URL is correct
   - Check network connectivity and firewall settings

4. **CORS errors in browser**
   - The app is configured to allow all origins
   - Check browser console for specific error details

### Debug Endpoints

Use the `/debug` endpoint to inspect your environment:

```bash
curl http://localhost:8000/debug
```

This returns information about:
- Environment variables
- File system paths
- Python version
- Working directory

### Health Checks

Monitor application health using:

```bash
# Basic health check
curl http://localhost:8000/health

# Kubernetes-style health check
curl http://localhost:8000/healthz

# Readiness check
curl http://localhost:8000/ready

# Simple ping
curl http://localhost:8000/ping
```

## Development

### Adding New Categories

To add new excuse categories, update the `categories` array in the React component:

```javascript
const categories = [
    'Running Late', 'Missed Meeting', 'Deadline', 
    'WFH/OOO', 'Social', 'Travel', 'New Category'
];
```

### Adding New Tones

Add new tones by updating the `tones` array:

```javascript
const tones = ['Sincere', 'Playful', 'Corporate', 'New Tone'];
```

### Customizing the UI

The application uses Tailwind CSS classes. Key customization points:

- **Colors**: Update the Tailwind config in `index.html`
- **Layout**: Modify the grid classes for different layouts
- **Styling**: Update component classes for visual changes

### Backend Extensions

The FastAPI backend is modular and can be extended:

- **New Endpoints**: Add routes in `src/app.py`
- **Middleware**: Add custom middleware for logging, auth, etc.
- **Models**: Extend Pydantic models for new data structures

## Security Considerations

- **API Tokens**: Never commit tokens to version control
- **CORS**: Configure appropriate origins for production
- **Input Validation**: All inputs are validated using Pydantic
- **Error Messages**: Sensitive information is not exposed in error messages

## Performance

- **Async Operations**: All I/O operations are asynchronous
- **CDN Resources**: React and Tailwind CSS loaded from CDN
- **Single Page**: No build process required for frontend
- **Efficient Rendering**: React hooks for optimal re-rendering

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally and with Databricks Apps
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the debug endpoint output
3. Check Databricks Apps logs
4. Create an issue with detailed error information

---

**Built with ❤️ for the Databricks community**
