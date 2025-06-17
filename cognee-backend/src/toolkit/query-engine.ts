import { VectorStoreRetriever } from '@langchain/core/vectorstores';
import { ChatGoogleGenerativeAI } from '@langchain/google-genai';
import { RetrievalQAChain, ConversationalRetrievalQAChain } from 'langchain/chains';
import { GEMINI_API_KEY } from '../config';
import {
  ChatPromptTemplate,
  HumanMessagePromptTemplate,
  SystemMessagePromptTemplate,
  MessagesPlaceholder,
} from '@langchain/core/prompts';
import { BaseMessage } from '@langchain/core/messages';


let llm: ChatGoogleGenerativeAI | undefined;

if (GEMINI_API_KEY) {
  llm = new ChatGoogleGenerativeAI({
    apiKey: GEMINI_API_KEY,
    modelName: 'gemini-2.0-flash', // As per user requirement
    temperature: 0.3, // Default, can be configured
  });
  console.log('ChatGoogleGenerativeAI (gemini-2.0-flash) initialized for query-engine.ts');
} else {
  console.warn('GEMINI_API_KEY is not set. Query engine will not be functional.');
}

function getInitializedLlm(): ChatGoogleGenerativeAI {
  if (!llm) {
    if (GEMINI_API_KEY) { // Attempt re-initialization
        llm = new ChatGoogleGenerativeAI({
            apiKey: GEMINI_API_KEY,
            modelName: 'gemini-2.0-flash',
            temperature: 0.3,
        });
        console.log('Re-initialized ChatGoogleGenerativeAI in query-engine.ts');
        return llm;
    }
    throw new Error('LLM not initialized. GEMINI_API_KEY is missing.');
  }
  return llm;
}

/**
 * Creates a RetrievalQAChain for question answering over a vector store.
 * @param retriever - The VectorStoreRetriever instance.
 * @returns A RetrievalQAChain instance.
 */
export function createRAGChain(retriever: VectorStoreRetriever) {
  const currentLlm = getInitializedLlm();

  // Optional: Define a custom prompt template for the RAG chain
  const qaPromptTemplate = ChatPromptTemplate.fromMessages([
    SystemMessagePromptTemplate.fromTemplate(
      "You are a helpful AI assistant. Use the following pieces of context to answer the question at the end. " +
      "If you don't know the answer, just say that you don't know, don't try to make up an answer. " +
      "Keep the answer concise and relevant to the question." +
      "

Context:
{context}"
    ),
    HumanMessagePromptTemplate.fromTemplate("Question: {question}
Answer:"),
  ]);

  console.log('Creating RAG chain...');
  const chain = RetrievalQAChain.fromLLM(
    currentLlm,
    retriever,
    {
      returnSourceDocuments: true, // As per user's TODO
      // prompt: qaPromptTemplate, // Optional: uncomment to use the custom prompt
      // verbose: true, // Optional: for debugging
    }
  );
  return chain;
}

/**
 * (Advanced) Creates a ConversationalRetrievalQAChain for question answering
 * with chat history over a vector store.
 * @param retriever - The VectorStoreRetriever instance.
 * @returns A ConversationalRetrievalQAChain instance.
 */
export function createConversationalChain(retriever: VectorStoreRetriever) {
  const currentLlm = getInitializedLlm();

  // Prompt for condensing the question based on chat history
  const questionGeneratorTemplate = ChatPromptTemplate.fromMessages([
    SystemMessagePromptTemplate.fromTemplate(
      "Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question, in its original language."
    ),
    new MessagesPlaceholder("chat_history"),
    HumanMessagePromptTemplate.fromTemplate("Follow Up Input: {question}
Standalone question:"),
  ]);

  // Prompt for answering the question based on context
  const qaPromptTemplate = ChatPromptTemplate.fromMessages([
    SystemMessagePromptTemplate.fromTemplate(
      "You are a helpful AI assistant. Use the following pieces of context to answer the question at the end. " +
      "If you don't know the answer, just say that you don't know, don't try to make up an answer. " +
      "Keep the answer concise and relevant to the question." +
      "

Context:
{context}"
    ),
    HumanMessagePromptTemplate.fromTemplate("Question: {question}
Helpful Answer:"),
  ]);


  console.log('Creating Conversational RAG chain...');
  const chain = ConversationalRetrievalQAChain.fromLLM(
    currentLlm,
    retriever,
    {
      returnSourceDocuments: true, // As per user's TODO
      // questionGeneratorChainOptions: { // More explicit way to pass prompt for question generation
      //   template: questionGeneratorTemplate, // This might not be the correct way to pass template directly
      //   llm: currentLlm, // Can specify a different LLM for question generation if needed
      // },
      // verbose: true, // Optional for debugging
      // qaChainOptions: { // For passing custom prompt to the QA part
      //   prompt: qaPromptTemplate, // This also might need specific structuring
      //   type: "stuff", // Default combine documents chain type
      // }
      // For more control over prompts in ConversationalRetrievalQAChain,
      // you might need to construct the underlying chains (questionGenerator and combineDocsChain) manually.
      // The fromLLM static method provides a simpler setup with default prompts.
      // For custom prompts, the documentation should be consulted for the exact structure.
      // The user's example snippet was simple, so this default setup should be close.
      // If specific prompts are needed, they can be passed via chainTypeAndInputKey / qaChainOptions according to docs.
      // For now, relying on default prompts for qa and question generation or simple overrides if they work.
      // The most straightforward way to customize prompts is to pass them when creating the chain.
      // Let's try with a simplified way to include custom prompts if fromLLM supports it directly or via qaPrompt
       qaPrompt: qaPromptTemplate, // For the document Q&A part
       questionGeneratorChainOptions: {
         prompt: questionGeneratorTemplate // For the standalone question generation
       }
    }
  );
  return chain;
}

console.log('query-engine.ts loaded');
