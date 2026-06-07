terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = "여기에_GCP_프로젝트_ID를_넣어주세요"
  region  = "asia-northeast3" # 서울 리전
}
