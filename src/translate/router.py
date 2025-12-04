import os
import logging
from typing import Optional

from fastapi import APIRouter, FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .utils import num_tokens_in_string, calculate_chunk_size, MAX_TOKENS_PER_CHUNK


router = APIRouter()

class TranslationRequest(BaseModel):
    id: int = Field(..., description="Translation task ID") 

class ChunksResponse(BaseModel):
    id: int = Field(..., description="Translation task ID")
    filename: str = Field(..., description="Output filename")
    status: str = Field(..., description="Translation status")
    chunks: Optional[list[str]] = Field(default=None, description="Translation result")
    error: Optional[str] = Field(default=None, description="Error message if failed")

@router.post("/chunks", response_model=ChunksResponse)
async def chunks(id: int = Form(...), filename: str = Form(...), file: UploadFile = File(...)):
    """文本分块API入口"""
    logging.info(f"收到文本分块请求: ID={id}, 源文件名={file.filename}, 输出文件名={filename}")
    try:  
        source_text = (await file.read()).decode("utf-8")


        num_tokens_in_text = num_tokens_in_string(source_text)
        logging.info(f"Number of tokens in source text: {num_tokens_in_text}")
 

        if num_tokens_in_text < MAX_TOKENS_PER_CHUNK: 
            logging.info("Translating text as a single chunk.")
            source_text_chunks = [source_text]
            logging.info("Finished single-chunk translation.") 

        else: 
            logging.info("Translating text as multiple chunks.")

            token_size = calculate_chunk_size(
                token_count=num_tokens_in_text, token_limit=MAX_TOKENS_PER_CHUNK
            )
            logging.info(f"Calculated chunk size: {token_size}")
 

            text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
                model_name="gpt-4",
                chunk_size=token_size,
                chunk_overlap=0,
            )

            source_text_chunks = text_splitter.split_text(source_text)
            logging.info(f"Split source text into {len(source_text_chunks)} chunks.")
 
            logging.info("Finished multi-chunk translation.") 


        return ChunksResponse(
            status="success",
            id=id,
            filename=filename,
            chunks=source_text_chunks
        )
        


    except Exception as e:
        logging.error(f"文本分块请求失败: ID={id}, 错误: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
