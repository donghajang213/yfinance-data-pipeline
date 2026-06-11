terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = "GCP ID"
  region  = "asia-northeast3" # 서울 리전
}
