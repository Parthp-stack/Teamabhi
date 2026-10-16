import api from './api';

export const learningService = {
  // Phase 2 Adaptive Question Endpoint
  async getNextQuestion(courseId = null) {
    const params = courseId ? { course_id: courseId } : {};
    const response = await api.get('/questions/next', { params });
    return response.data;
  },

  // Submit Answer to Question
  async submitAttempt(questionId, selectedAnswer, timeTaken = 0.0) {
    const response = await api.post(`/questions/${questionId}/attempt`, {
      selected_answer: selectedAnswer,
      time_taken: timeTaken,
    });
    return response.data;
  },

  // Dynamic Learning Path
  async getLearningPath() {
    const response = await api.get('/learning/path');
    return response.data;
  },

  // Student Mastery Overview
  async getStudentMastery() {
    const response = await api.get('/student/mastery');
    return response.data;
  },

  // Weak Concepts
  async getWeakConcepts() {
    const response = await api.get('/student/weak-concepts');
    return response.data;
  },

  // Interactive Concept Graph for React Flow
  async getConceptGraph(studentId = null) {
    const params = studentId ? { student_id: studentId } : {};
    const response = await api.get('/concepts/graph', { params });
    return response.data;
  },

  // Concept Detail
  async getConceptDetail(conceptId, studentId = null) {
    const params = studentId ? { student_id: studentId } : {};
    const response = await api.get(`/concepts/${conceptId}`, { params });
    return response.data;
  },

  async getMyMastery() {
    const response = await api.get('/student/mastery');
    return response.data;
  },
};

export const masteryService = learningService;

export const aiService = {
  async explainConcept(concept, studentMastery = 0.0, difficulty = 'MEDIUM') {
    const response = await api.post('/ai/explain-concept', {
      concept,
      student_mastery: studentMastery,
      difficulty,
    });
    return response.data;
  },

  async generateQuestion(concept, difficulty = 'MEDIUM', questionType = 'MCQ') {
    const response = await api.post('/ai/generate-question', {
      concept,
      difficulty,
      question_type: questionType,
    });
    return response.data;
  },

  async generatePractice(concept, studentWeakAreas = []) {
    const response = await api.post('/ai/generate-practice', {
      concept,
      student_weak_areas: studentWeakAreas,
    });
    return response.data;
  },
};

export const trainerService = {
  async getBasicOverview() {
    const response = await api.get('/trainer/overview');
    return response.data;
  },
};
