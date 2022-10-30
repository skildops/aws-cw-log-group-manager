data "template_file" "retention" {
  template = file("../src/retention.py")
}

data "template_file" "encryption" {
  template = file("../src/encryption.py")
}

data "archive_file" "retention" {
  type        = "zip"
  output_path = "${path.module}/retention.zip"
  source {
    content  = data.template_file.retention.rendered
    filename = "retention.py"
  }
}

data "archive_file" "encryption" {
  type        = "zip"
  output_path = "${path.module}/encryption.zip"
  source {
    content  = data.template_file.encryption.rendered
    filename = "encryption.py"
  }
}
