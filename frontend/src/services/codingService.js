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

  async recordWarning(sessionId, warningData) {
    const response = await api.post(`/sessions/${sessionId}/warning`, warningData);
    return response.data;
  },
};

export const assessmentService = {
  async startAttempt(assessmentId, assessmentType = 'ADAPTIVE_QUIZ', options = {}) {
    const response = await api.post('/assessments/start', {
      assessment_id: String(assessmentId),
      assessment_type: assessmentType,
      ...options,
    });
    return response.data;
  },

  async getState(attemptId) {
    const response = await api.get(`/assessments/${attemptId}/state`);
    return response.data;
  },

  async navigate(attemptId, targetQuestionNumber) {
    const response = await api.post(`/assessments/${attemptId}/navigate`, {
      target_question_number: targetQuestionNumber,
    });
    return response.data;
  },

  async saveAnswer(attemptId, questionNumber, selectedAnswer, timeTaken = 0.0) {
    const response = await api.post(`/assessments/${attemptId}/save-answer`, {
      question_number: questionNumber,
      selected_answer: selectedAnswer,
      time_taken: timeTaken,
    });
    return response.data;
  },

  async nextQuestion(attemptId) {
    const response = await api.post(`/assessments/${attemptId}/next-question`);
    return response.data;
  },

  async previousQuestion(attemptId) {
    const response = await api.post(`/assessments/${attemptId}/previous-question`);
    return response.data;
  },

  async finishAttempt(attemptId) {
    const response = await api.post(`/assessments/${attemptId}/finish`);
    return response.data;
  },

  async getAttemptAnalysis(attemptId) {
    const response = await api.get(`/student/attempts/${attemptId}/analysis`);
    return response.data;
  },

  async getStudentAttempts(assessmentId = null) {
    const response = await api.get('/student/attempts', {
      params: assessmentId ? { assessment_id: assessmentId } : {},
    });
    return response.data;
  },

  async getTrainerAttempts(params = {}) {
    const response = await api.get('/trainer/attempts', { params });
    return response.data;
  },

  async getAttemptTimeline(attemptId) {
    const response = await api.get(`/trainer/attempts/${attemptId}/timeline`);
    return response.data;
  },

  async validateMCQ(mcqData) {
    const response = await api.post('/questions/validate', mcqData);
    return response.data;
  },
};

export const integrityService = {
  // Requirement 4, 7, 8: Dedicated Student Integrity Table & Database Summary Cards
  async getIntegrityEvents(params = {}) {
    const response = await api.get('/integrity/events', { params });
    return response.data;
  },

  async recordIntegrityEvent(eventData) {
    const response = await api.post('/integrity/events', eventData);
    return response.data;
  },

  async getIntegritySummary(studentId = null) {
    const params = studentId ? { student_id: studentId } : {};
    const response = await api.get('/integrity/summary', { params });
    return response.data;
  },

  async getDashboardSessions(params = {}) {
    const response = await api.get('/integrity/sessions', { params });
    return response.data;
  },

  async getSessionTimeline(sessionId) {
    const response = await api.get(`/integrity/sessions/${sessionId}/timeline`);
    return response.data;
  },

  async getTypingRhythm(sessionId) {
    const response = await api.get(`/integrity/sessions/${sessionId}/rhythm`);
    return response.data;
  },

  async getRevisionComparison(sessionId, revisionId) {
    const response = await api.get(`/integrity/sessions/${sessionId}/revisions/${revisionId}`);
    return response.data;
  },

  async submitTrainerReview(sessionId, reviewData) {
    const response = await api.post(`/integrity/sessions/${sessionId}/review`, reviewData);
    return response.data;
  },

  async triggerCleanup(retentionDays) {
    const response = await api.post('/integrity/cleanup', null, { params: { retention_days: retentionDays } });
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
