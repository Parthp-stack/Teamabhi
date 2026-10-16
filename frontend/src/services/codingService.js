import api from './api';

export const codingService = {
  async getProblems() {
    const response = await api.get('/coding/problems');
    return response.data;
  },

  async getProblem(id) {
    const response = await api.get(`/coding/problems/${id}`);
    return response.data;
  },

  async runCode(problemId, language, sourceCode) {
    const response = await api.post('/coding/run', {
      problem_id: problemId,
      language: language,
      source_code: sourceCode,
    });
    return response.data;
  },

  async submitCode(problemId, language, sourceCode, sessionId = null) {
    const response = await api.post('/coding/submit', {
      problem_id: problemId,
      language: language,
      source_code: sourceCode,
      session_id: sessionId,
    });
    return response.data;
  },

  async getVivaQuestions(submissionId) {
    const response = await api.get(`/explanation/submission/${submissionId}/questions`);
    return response.data;
  },

  async submitVivaAnswers(answers) {
    // answers is array of { question_id, student_answer }
    const response = await api.post('/explanation/submit', { answers });
    return response.data;
  },

  async getVivaResults(submissionId) {
    const response = await api.get(`/explanation/submission/${submissionId}/results`);
    return response.data;
  },
};

export const sessionService = {
  async startSession(assessmentId) {
    const response = await api.post('/sessions/start', { assessment_id: assessmentId });
    return response.data;
  },

  async recordEventsBatch(sessionId, events) {
    const response = await api.post(`/sessions/${sessionId}/events`, { events });
    return response.data;
  },

  async endSession(sessionId) {
    const response = await api.post(`/sessions/${sessionId}/end`);
    return response.data;
  },

  async getReplay(sessionId) {
    const response = await api.get(`/sessions/${sessionId}/replay`);
    return response.data;
  },

  async getSignals(sessionId) {
    const response = await api.get(`/integrity/sessions/${sessionId}/signals`);
    return response.data;
  },
};

export const trainerService = {
  async getDashboardOverview() {
    const response = await api.get('/trainer/dashboard');
    return response.data;
  },

  async getStudentDeepDive(studentId) {
    const response = await api.get(`/trainer/student/${studentId}`);
    return response.data;
  },
};
